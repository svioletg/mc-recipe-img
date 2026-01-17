import json
import os
import platform
import re
from collections import OrderedDict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Literal
from zipfile import ZipFile

from PIL import Image
from pydantic import BaseModel

from mc_recipe_img import ASSETS_DIR, Point, crafting_types, file_cache, logger, mem_cache
from mc_recipe_img.util import ensure_list, partitioned

DEFAULT_MCPATH_WINDOWS : Path = Path.home() / 'AppData/Roaming/.minecraft'
DEFAULT_MCPATH_MAC     : Path = Path.home() / 'Library/Application Support/minecraft'
DEFAULT_MCPATH_LINUX   : Path = Path.home() / '.minecraft'

DATAPACK_FORMAT_VERSIONS: OrderedDict[int | float, list[str]] = OrderedDict({
    4: [
        '1.13',
        '1.13.1',
        '1.13.2',
        '1.14',
        '1.14.1',
        '1.14.2',
        '1.14.3',
        '1.14.4',
    ],
    5: [
        '1.15',
        '1.15.1',
        '1.15.2',
        '1.16',
        '1.16.1',
    ],
    6: [
        '1.16.2',
        '1.16.3',
        '1.16.4',
        '1.16.5',
    ],
    7: [
        '1.17',
        '1.17.1',
    ],
    8: [
        '1.18',
        '1.18.1',
    ],
    9: [
        '1.18.2',
    ],
    10: [
        '1.19',
        '1.19.1',
        '1.19.2',
        '1.19.3',
    ],
    12: [
        '1.19.4',
    ],
    15: [
        '1.20',
        '1.20.1',
    ],
    18: [
        '1.20.2',
    ],
    26: [
        '1.20.3',
        '1.20.4',
    ],
    41: [
        '1.20.5',
        '1.20.6',
    ],
    48: [
        '1.21',
        '1.21.1',
    ],
    57: [
        '1.21.2',
        '1.21.3',
    ],
    61: [
        '1.21.4',
    ],
    71: [
        '1.21.5',
    ],
    80: [
        '1.21.6',
    ],
    81: [
        '1.21.7',
        '1.21.8',
    ],
    88.0: [
        '1.21.9',
        '1.21.10',
    ],
    94.1: [
        '1.21.11',
    ],
})

class PackMCMeta(BaseModel):
    # Based on the information given here: https://minecraft.wiki/w/Pack.mcmeta

    class _Pack(BaseModel):
        description: str | list[dict[str, Any]] | dict[str, Any]
        pack_format: int | None = None
        min_format: int | tuple[int, int] | None = None
        max_format: int | tuple[int, int] | None = None
        supported_formats: int | list[int] | dict[str, int] | None = None

    class _Features(BaseModel):
        enabled: list[str]

    pack: _Pack
    features: _Features | None = None

class Datapack:
    def __init__(self, dir_path: str | Path, mc_versions: list[str]) -> None:
        """
        :param dir_path: Path to the datapack's directory, i.e. the directory that contains `data/` and `pack.mcmeta`.
        :param mc_versions: Which Minecraft versions this datapack supports, used for things like expanding vanilla
            tags with `Datapack.expand_tag()`. If `None`, it is set to list of versions from oldest to newest that are
            supported by the pack's minimum pack format.
        """
        self.dir_path: Path = Path(dir_path)
        if not self.dir_path.is_dir():
            raise NotADirectoryError(f'Not a directory or does not exist: {self.dir_path}')
        if not (fp.stem for fp in self.dir_path.glob('*/') if fp.stem == 'data'):
            raise ValueError(f'Failed to find "data" subdirectory in datapack path: {self.dir_path}')

        with open(self.dir_path / 'pack.mcmeta', 'r', encoding='utf-8') as f:
            self.meta = PackMCMeta(**json.load(f))

        self.mc_versions: list[str] = mc_versions

        self.recipes: dict[Path, dict[str, Any]] = {}
        self.tags: dict[Path, list[str]] = {}

        self.reload()

    def __repr__(self) -> str:
        return f'<Datapack at {self.dir_path}; {len(self.recipes)} recipes, {len(self.tags)} tags>'

    def expand_tag(self, tag: str) -> list[str]:
        """Returns the resources associated with a given tag."""
        tag = tag.removeprefix('#')
        if (':' not in tag) or tag.startswith('minecraft:'):
            # Assume no namespace means the minecraft namespace
            # Expand minecraft-namespaced tag from JAR file namelist
            return expand_vanilla_tag(tag, self.mc_versions)
        return self.tags[self.resource_to_path(tag)]

    def find_required_textures(self, *assets_sources: str | Path) -> dict[str, Path]:
        """
        Returns a dictionary of resource keys to their texture paths that will be needed for every recipe in `pack`.
        """
        assets_sources = assets_sources or tuple(self.mc_versions)

        logger.info('Searching datapack recipes for items...')

        # Start with coal and blaze powder for smelting and brewing recipes
        resources: list[str] = ['minecraft:coal', 'minecraft:blaze_powder']

        for rpath, rdata in self.recipes.items():
            logger.debug(f'Found recipe: {rpath}')
            for key in (
                    'key', 'ingredients', 'ingredient', 'input', 'material', 'addition', 'base', 'template', 'result',
                ):
                value: dict[str, Any] | list[str] | str | None = rdata.get(key)
                if value is None:
                    continue
                if isinstance(value, str):
                    resources.append(value)
                elif isinstance(value, list):
                    resources.extend(value)
                elif isinstance(value, dict):
                    if key == 'result':
                        resources.append(value['id'])
                    resources.extend(item for _, item in value.items() if isinstance(item, str))

        tags, resources = partitioned(lambda i: i[0] == '#', (i if ':' in i else f'minecraft:{i}' for i in resources))

        # Expand tags
        resources.extend([item for t in tags for item in self.expand_tag(t)])

        return {r:texpath for r in set(resources) if (texpath := find_item_texture(r, *assets_sources))}

    def path_to_resource(self, fp: str | Path) -> str:
        """
        Returns the resource key (e.g. `minecraft:oak_planks`) for a JSON file path in this datapack.
        If the resource is a tag, `#` will be prepended to the returned string.
        """
        fp = Path(fp).relative_to(self.dir_path / 'data')
        return f'{'#' if 'tags' in fp.parts else ''}{fp.parts[0]}:{fp.stem}'

    def reload(self) -> None:
        """Re-scans the datapack for recipes, tags, etc. and replaces the object's corresponding attributes"""
        for fp in self.dir_path.rglob('*.json'):
            relpath: Path = fp.relative_to(self.dir_path / 'data')
            category = relpath.parts[1]
            if category == 'recipe':
                with open(fp, 'r', encoding='utf-8') as f:
                    self.recipes[fp] = json.load(f)
            elif category == 'tags':
                with open(fp, 'r', encoding='utf-8') as f:
                    self.tags[fp] = json.load(f)['values']

    def render_recipes(self,  # noqa: PLR0915
            texture_map: dict[str, Path],
            recipe_filter: str | re.Pattern[str] | list[str] | None = None,
        ) -> dict[str, Image.Image]:
        """
        Renders recipe images for each recipe in the datapack, sourcing its textures for each item from `texture_map`,
        and optionally restricting the recipes to render with `recipe_filter`.

        :returns rendered: A dictionary of recipe names (including namespace) to PIL `Image` objects.

        :param texture_map: A dictionary of resource keys (`<namespace>:<item>`) to texture paths on disk.
        :param recipe_filter: An optional filter for what recipes to render. A single string will be interpereted as a
            regex pattern to test each recipe name (including namespace) against, always matching from the beginning of
            the name. If a `list` of strings is given, only recipe names *exactly matching* those strings are rendered.
        """
        loaded_base_imgs: dict[Path, Image.Image] = {
            fp:Image.open(fp, 'r')
            for fp in [
                ASSETS_DIR / 'base_blasting.png',
                ASSETS_DIR / 'base_brewing.png',
                ASSETS_DIR / 'base_crafting_2x2.png',
                ASSETS_DIR / 'base_crafting_3x3.png',
                ASSETS_DIR / 'base_smelting.png',
                ASSETS_DIR / 'base_smithing.png',
                ASSETS_DIR / 'base_smithing.png',
                ASSETS_DIR / 'base_smoking.png',
            ]
        }

        rendered: dict[str, Image.Image] = {}
        if isinstance(recipe_filter, str):
            recipe_filter = re.compile(recipe_filter)

        texture_cache: dict[str, Image.Image] = {}

        def get_texture_or_cached(item: str) -> Image.Image:
            if item.startswith('#'):
                # Handle item tags
                # TODO: Option to make this an animated gif cycling through each item
                item = self.expand_tag(item.removeprefix('#'))[0]
            if ':' not in item:
                item = 'minecraft:' + item
            if not (texture := texture_cache.get(item)):
                texture_src: Path | None = texture_map.get(item)
                if not texture_src:
                    logger.warning(f'Missing texture: {item}')
                    texture_src = ASSETS_DIR / 'missing.png'
                texture = Image.open(texture_map.get(item, ASSETS_DIR / 'missing.png'))
                texture = texture.convert(mode='RGBA')
                texture_cache[item] = texture
            return texture

        for rpath, rdata in self.recipes.items():
            logger.debug(f'Rendering recipe: {rpath}')
            rtype: str | None = rdata.get('type')
            if not rtype:
                logger.warning(f'Recipe has no "type" field: {rpath}')
                continue

            rname: str = self.path_to_resource(rpath)
            if recipe_filter:
                if isinstance(recipe_filter, re.Pattern) and (not recipe_filter.match(rname)):
                    logger.debug(f'Recipe name did not match pattern "{recipe_filter}": {rname}')
                    continue
                if isinstance(recipe_filter, list) and (rname not in recipe_filter):
                    logger.debug(f'Recipe name not part of filter list: {rname}')
                    continue

            recipe_img: Image.Image | None = None

            rtype = rtype.removeprefix('minecraft:')
            match rtype:
                case 'blasting' | 'smelting' | 'smoking':
                    ingredient: str | list[str] = rdata['ingredient']
                    fuel: str = 'minecraft:coal'
                    result: str = rdata['result']['id']

                    match rtype:
                        case 'blasting':
                            imap = crafting_types.BLASTING
                        case 'smelting':
                            imap = crafting_types.SMELTING
                        case 'smoking':
                            imap = crafting_types.SMOKING
                        case _:
                            raise ValueError(rtype)

                    recipe_img = loaded_base_imgs[imap.base_path].copy()

                    raise NotImplementedError
                case 'crafting_shaped':
                    pattern: dict[Point, str] = {
                        (n, m): rdata['key'][key]
                        for n, row in enumerate(rdata['pattern'])
                        for m, key in enumerate(row)
                    }

                    imap = crafting_types.CRAFTING_GRID_3 \
                        if any(2 in point for point in pattern) \
                        else crafting_types.CRAFTING_GRID_2  # noqa: PLR2004
                    recipe_img = loaded_base_imgs[imap.base_path].copy()

                    for (row, col), item in pattern.items():
                        texture: Image.Image = get_texture_or_cached(item)
                        recipe_img.paste(texture, imap.inputs[row][col], texture)

                    texture = get_texture_or_cached(rdata['result']['id'])
                    recipe_img.paste(texture, imap.result, texture)
                case 'crafting_shapeless':
                    ingredients: list[str] = rdata['ingredients']

                    imap = crafting_types.CRAFTING_GRID_3 if len(ingredients) > 4 else crafting_types.CRAFTING_GRID_2  # noqa: PLR2004
                    recipe_img = loaded_base_imgs[imap.base_path].copy()

                    for point, item in zip(imap.inputs_shapeless, ingredients, strict=False):
                        texture: Image.Image = get_texture_or_cached(item)
                        recipe_img.paste(texture, point, texture)

                    texture = get_texture_or_cached(rdata['result']['id'])
                    recipe_img.paste(texture, imap.result, texture)
                case 'crafting_transmute':
                    logger.warning(NotImplemented)
                case 'smithing_transform' | 'smithing_trim':
                    raise NotImplementedError
                case _:
                    logger.warning(f'Unsupported or unrecognized recipe type: {rtype!r}')

            if recipe_img:
                rendered[rname] = recipe_img

        for _, img in loaded_base_imgs.items():
            img.close()

        return rendered

    def resource_to_path(self, resource: str) -> Path:
        """
        Returns the JSON file path for a resource key (e.g. `minecraft:oak_planks`) in this datapack.
        `resource` must begin with `#` to get a tag's path.
        """
        namespace, name = resource.removeprefix('#').split(':')
        search_pool: Iterable[Path] = self.tags if resource[0] == '#' else self.recipes
        for fp in search_pool:
            if fp.relative_to(self.dir_path / 'data').parts[0] != namespace:
                continue
            if fp.stem == name:
                return fp
        raise FileNotFoundError(f'Failed to find file path for resource key: {resource}')

def get_mc_home() -> Path:
    """
    Returns the user's Minecraft installation directory, first checking the `MC_HOME` environment variable, then
    returning the default for the OS in use if this variable is unset.
    """
    if (env_val := os.getenv('MC_HOME')):
        return Path(env_val)
    match system := platform.system():
        case 'Windows':
            return DEFAULT_MCPATH_WINDOWS
        case 'Darwin':
            return DEFAULT_MCPATH_MAC
        case 'Linux':
            return DEFAULT_MCPATH_LINUX
        case _:
            raise ValueError(f'Unexpected OS value: {system}')

def get_mc_version_jar(version: str, dot_minecraft: Path | None = None) -> Path:
    """
    Returns a path to the given Minecraft version JAR file.

    :param dot_minecraft: A path to the `.minecraft` directory where the version should be located.
        If `None`, the `MC_HOME` enviornment variable is used if set, otherwise the default path for the current OS is
        used according to `get_default_mcpath()`.
    """
    dot_minecraft = dot_minecraft or get_mc_home()
    return dot_minecraft / f'versions/{version}/{version}.jar'

def get_jar_namelist(jar_path: str | Path, *, only: Literal['textures', 'tags'] | None = None) -> list[str]:
    """
    Returns the list of item/block texture or tag names in the given JAR file, returning them from the cache if
    available, otherwise getting them from the JAR, caching the list, and returning it.
    """
    jar_path = Path(jar_path).absolute()
    if jar_path.suffix != '.jar':
        raise ValueError(f'Expected `.jar` file suffix: {jar_path}')

    jar_names: list[str] = []

    file_cache_key: str = f'jar_namelist/{jar_path.stem}.json'
    cached_names: list[str] = file_cache \
        .get(file_cache_key, {}, parser=json.loads) \
        .get('namelist', [])
    if cached_names:
        jar_names = cached_names
    else:
        with ZipFile(jar_path) as jar:
            jar_names = [
                name for name in jar.namelist()
                if name.startswith(
                    ('assets/minecraft/textures/block/', 'assets/minecraft/textures/item/', 'data/minecraft/tags/'),
                )
            ]
        file_cache.store(file_cache_key, json.dumps({'namelist': jar_names}))

    match only:
        case None:
            return jar_names
        case 'textures':
            return [name for name in jar_names if name.startswith('assets/minecraft/textures/')]
        case 'tags':
            return [name for name in jar_names if name.startswith('data/minecraft/tags/')]
        case _:
            raise ValueError(f'Unexpected only value: {only!r}')

def extract_textures_from_jar(
        jar_path: str | Path,
        out_dir: str | Path,
        paths: Sequence[str] | re.Pattern[str] | str | None = None,
        *,
        overwrite: bool = False,
        dry: bool = False,
    ) -> list[Path]:
    """
    Extracts images from the `block` and `item` Minecraft JAR texture folders to `out_dir`, preserving the archive file
    structure. If `jar_path` does not end in `.jar`, `ValueError` is raised. The `paths` option can be given to specify
    which files to extract, otherwise all available files are extracted.

    :param paths: A `Sequence` of strings, a compiled regex pattern, or a regex pattern as a regular string to filter
        the extracted files by. Only names in the archive which are in the sequence or match the pattern will be
        extracted.
    :param overwrite: Whether to overwrite any files that already exist at a given archive item's extraction
        destination. This will still raise an error if an extraction destination exists and is a directory.
    :param dry: Performs a dry run if `True`, meaning nothing will get extracted from the JAR.

    :returns extracted: A list of destination paths the files were extracted to.

    :raises IsADirectoryError: Raised if the extraction destination of an archive item already exists and is a
        directory.
    """
    jar_path = Path(jar_path).resolve()
    if jar_path.suffix != '.jar':
        raise ValueError(f'Expected `.jar` file suffix: {jar_path}')

    out_dir = Path(out_dir).resolve()
    if not out_dir.is_dir():
        raise NotADirectoryError(f'Not a directory or does not exist: {out_dir}')

    if isinstance(paths, str):
        paths = re.compile(paths)

    texture_name_regex: re.Pattern[str] = re.compile(r"assets/minecraft/textures/(block|item)/.*\.png$")
    extracted: list[Path] = []

    with ZipFile(jar_path) as jar:
        for name in jar.namelist():
            if isinstance(paths, re.Pattern) and not paths.match(name):
                continue
            if isinstance(paths, Sequence) and (name not in paths):
                continue
            if not texture_name_regex.match(name):
                continue
            dest: Path = Path(out_dir, name)
            if dest.is_dir():
                logger.warning(f'Destination exists and is a directory: {dest}')
                continue
            if (not overwrite) and dest.is_file():
                logger.info(f'Destination file already exists: {dest}')
                continue
            logger.info(f'Extracting: {name} -> {dest}')
            if not dry:
                jar.extract(name, out_dir)
            extracted.append(dest)

    return extracted

def expand_vanilla_tag(tag: str, mc_versions: str | list[str]) -> list[str]:
    """
    Returns the values associated with a vanilla (`minecraft` namespace) tag by attempting to find and read it from one
    the associated JAR files for the versions given in `mc_versions`.
    """
    mc_versions = ensure_list(mc_versions)
    tag_stem: str = tag.split(':')[-1]

    for jar_path in (get_mc_version_jar(v) for v in mc_versions):
        if jar_path.is_file():
            break
    else:
        raise ValueError(
            f'Failed to find installed JARs for any of these versions: {', '.join(mc_versions)}',
        )

    mem_cache_key: str = f'vanilla_tag/{jar_path.stem}/{tag_stem}'
    if cached := mem_cache.data.get(mem_cache_key):
        return cached['values']

    file_cache_key: str = mem_cache_key + '.json'
    if cached := file_cache.get(file_cache_key, parser=json.loads):
        mem_cache.data[mem_cache_key] = cached
        return cached['values']

    for name in map(Path, get_jar_namelist(jar_path, only='tags')):
        if name.stem == tag_stem:
            break
    else:
        raise ValueError(f'Failed to find vanilla tag "#{tag!r}" in JAR file: {jar_path}')

    # Read the tag JSON from the JAR and cache it before returning
    with ZipFile(jar_path) as jar:
        values: list[str] = json.loads(jar.read(str(name)).decode('utf-8'))['values']

    mem_cache.data[mem_cache_key] = {'values': values}
    file_cache.store(file_cache_key, json.dumps({'values': values}))
    return values

def find_item_texture(item_id: str, *assets_sources: str | Path) -> Path | None:
    """
    Returns the file path for this item's texture found in any of `assets_sources`. If a namespace is not given in
    `item_id`, it will be assumed to be `minecraft`. Returns `None` if no texture path could be found. If the texture
    path found is inside a JAR file (if one of `assets_sources` is a version number), the returned path will include
    the path to the JAR followed by a double colon, then the texture path inside the JAR, indicating that the file
    needs to be extracted.

    If the item texture could not found under `textures/item`, `textures/block` will be searched instead.

    :param item_id: An item name, with or without namespace;
        e.g. `minecraft:oak_planks`, `oak_planks`
    :param assets_sources: A list of `assets/` directories to check for the texture, in order of priority. Can also be
        Minecraft version numbers, in this case the corresponding JAR file is located and searched for the texture.
    """
    namespace: str = 'minecraft' if ':' not in item_id else item_id.split(':')[0]
    stem: str = item_id.split(':')[-1]

    if not assets_sources:
        raise ValueError('Need at least one value for assets_sources')

    for src in map(Path, assets_sources):
        item_stem: str = f'{namespace}/textures/item/{stem}.png'
        block_stem: str = f'{namespace}/textures/block/{stem}.png'

        if src.parts[-1] != 'assets':
            logger.debug(f'Source does not end in "assets", assuming it\'s a Minecraft version: {src}')
            jar_src: Path = get_mc_version_jar(str(src))
            mem_cache_key: str = f'jar_namelist/{jar_src.stem}'
            jar_names: list[str] = mem_cache.get_or_store(mem_cache_key, lambda jar=jar_src: get_jar_namelist(jar))

            if (tpath := f'assets/{item_stem}') in jar_names:
                return Path(str(jar_src) + f'::{tpath}')
            if (tpath := f'assets/{block_stem}') in jar_names:
                return Path(str(jar_src) + f'::{tpath}')
        else:
            if not src.is_dir():
                logger.warning(f'Source directory does not exist: {src}')
                continue
            if (tpath := src / item_stem).is_file():
                return tpath
            if (tpath := src / block_stem).is_file():
                return tpath

    return None
