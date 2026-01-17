from pathlib import Path

from mc_recipe_img import logger
from mc_recipe_img.mc import Datapack, find_item_texture
from mc_recipe_img.util import partitioned


def find_required_textures(pack: Datapack, *assets_sources: str | Path) -> list[Path]:
    """Returns a list of paths to textures that will be needed for every recipe in `pack`."""
    assets_sources = assets_sources or tuple(pack.mc_versions)

    logger.info('Searching datapack recipes for items...')

    resources: list[str] = []

    for fp, data in pack.recipes.items():
        logger.debug(f'Found recipe: {fp}')
        for key in ('key', 'ingredients', 'ingredient', 'input', 'material', 'addition', 'base', 'template'):
            value: dict[str, str | int] | list[str] | str | None = data.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                resources.append(value)
            elif isinstance(value, list):
                resources.extend(value)
            elif isinstance(value, dict):
                resources.extend(item for _, item in value.items() if isinstance(item, str))

    tags, resources = partitioned(lambda i: i[0] == '#', (i if ':' in i else f'minecraft:{i}' for i in resources))

    # Expand tags
    resources.extend([item for t in tags for item in pack.expand_tag(t)])

    return [texpath for r in set(resources) if (texpath := find_item_texture(r, *assets_sources))]
