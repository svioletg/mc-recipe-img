import shutil
from enum import Enum
from pathlib import Path
from typing import Annotated, Never

import typer
from PIL import Image
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.prompt import Confirm
from rich.theme import Theme
from tabulate2 import tabulate

from mc_recipe_img import FILE_CACHE, USER_CACHE_DIR, init_logger, logger, mc
from mc_recipe_img.util import parse_envvar_paths, partitioned


class LogLevel(str, Enum):
    DEBUG   = 'DEBUG'
    INFO    = 'INFO'
    WARNING = 'WARNING'
    ERROR   = 'ERROR'

#region RICH SETUP

def setup_rich_console() -> Console:
    class Highlighter(RegexHighlighter):
        base_style = 'autohl.'
        highlights = [ # noqa: RUF012
            r"\b(?P<true>True)\b",
            r"\b(?P<false>False)\b",
            r"\b(?P<number>\d+(?:[,\.]\d+|)*)\b",
            r"\b(?P<option>--\w+)\b",
        ]

    theme = Theme({
        'info' : 'cyan',
        'ok'   : 'bright_green',
        'warn' : 'yellow',
        'err'  : 'red',
        'arg'  : 'bright_yellow',
        'path' : 'magenta',

        'autohl.true'   : 'green',
        'autohl.false'  : 'red',
        'autohl.number' : 'cornflower_blue',
        'autohl.option'  : 'bright_yellow',
    })

    return Console(
        highlighter=Highlighter(),
        theme=theme,
    )

console: Console = setup_rich_console()

#endregion RICH SETUP

def abort(msg: str = 'Aborting.', *, code: int = 1) -> Never:
    """Prints a message and raises `SystemExit` with the given code."""
    console.print(f'{msg}')
    raise SystemExit(code)

cligroup_cache = typer.Typer(no_args_is_help=True)

@cligroup_cache.command()
def show() -> None:
    """Prints the path to ths script's cache directory."""
    console.print(USER_CACHE_DIR)

@cligroup_cache.command()
def clear(
        *,
        confirm: Annotated[bool, typer.Option(
            '--yes', '-y', help='Skips the confirmation prompt and proceeds automatically.',
        )] = False,
    ) -> None:
    """Removes all directories and files in the script's cache directory."""
    to_rm: list[Path] = list(USER_CACHE_DIR.rglob('*'))

    if not to_rm:
        console.print('Cache is empty; nothing removed.')
        return

    logger.debug(f'{len(to_rm)} files in cache:\n    {'\n    '.join(map(str, to_rm))}')
    if not (confirm or Confirm.ask(f'Delete all {len(to_rm)} cached files?')):
        abort()

    to_rm_files, to_rm_dirs = partitioned(lambda fp: fp.is_file(), to_rm)

    # Remove files first since rmdir() requires the directory to be empty
    for fp in to_rm_files:
        logger.debug(f'Removing file: {fp}')
        fp.unlink()
    for dp in to_rm_dirs:
        logger.debug(f'Removing directory: {dp}')
        dp.rmdir()

    console.print('Cache cleared.')

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(cligroup_cache, name='cache')

@cli.command()
def run(
        datapack_dir: Annotated[Path, typer.Option(
            '--pack', '-i', envvar='DATAPACK_DIR', help='Path to the datapack to use recipes from.',
        )],
        output_dir: Annotated[Path, typer.Option(
            '--out', '-o', help='Directory to save the generated recipe images to.',
        )],
        textures_sources: Annotated[list[Path], typer.Option(
            '--textures', '-t', envvar='MC_ASSETS_SRC', default_factory=list,
            help='A Minecraft version number, or a path to the extracted Minecraft texture assets to use.'
                + ' If giving a path, the final path component needs to be "assets", or else it is treated as a'
                + ' Minecraft version. Multiple values can be given from highest to lowest priority. If option values'
                + ' while the environment variable is also set, the option values will take highest priority.',
        )],
    ) -> None:
    """Runs the main script."""

    #region MANAGE ARGUMENTS

    datapack_dir = datapack_dir.absolute()
    if not datapack_dir.is_dir():
        raise NotADirectoryError(f'Not a directory, or does not exist: {datapack_dir}')
    if not (datapack_dir / 'data').is_dir():
        raise NotADirectoryError(f'Datapack has no "data" subdirectory: {datapack_dir}')

    if not textures_sources:
        abort('[err]ERROR: No textures source(s) given. Either set the MC_ASSETS_SRC environment variable, or use the'
            + ' --textures/-t option to supply some.[/]')

    env_textures_sources: list[Path] = parse_envvar_paths('MC_ASSETS_SRC')
    if textures_sources != env_textures_sources:
        # If the option was used, the enviornment var values won't be present, so tack them onto the end
        textures_sources.extend(env_textures_sources)

    mc_versions: list[str] = [str(v) for v in textures_sources if v.stem != 'assets']

    if not mc_versions:
        abort('[err]ERROR: At least one Minecraft version needs to be given with --textures/-t.[/]')

    output_dir = output_dir.absolute()

    #endregion MANAGE ARGUMENTS

    #region ANALYZE RECIPES, COLLECT TEXTURES

    pack: mc.Datapack = mc.Datapack(datapack_dir, mc_versions)
    texture_map: dict[str, Path] = pack.get_texture_map(*textures_sources, extract=True)

    #endregion ANALYZE RECIPES, COLLECT TEXTURES

    #region RENDER RECIPES

    logger.debug(f'Texture map:\n{tabulate(texture_map.items())}')

    rendered: dict[str, Image.Image] = pack.render_recipes()

    logger.info(f'Saving {len(rendered)} images to: {output_dir}')

    for rname, img in rendered.items():
        namespace, name = rname.split(':')
        dest: Path = output_dir / namespace / f'{name}.png'
        logger.debug(f'Saving image for recipe {rname} to: {dest}')
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)
        img.save(output_dir / namespace / f'{name}.png')

    logger.info('Done!')

    #endregion RENDER RECIPES

@cli.callback()
def main(
        *,
        log_level: Annotated[LogLevel, typer.Option(
            '--log-level', '-l', help='Sets the log level.',
            case_sensitive=False,
        )] = LogLevel.INFO,
        log_file: Annotated[Path | None, typer.Option(
            '--log-file', help='Saves debug logs to this file.',
        )] = None,
        debug: Annotated[bool, typer.Option(
            '-D', help='Shortcut for `--log-level=debug`. Overrides any value given to --log-level.',
            is_flag=True,
        )] = False,
        clear_cache: Annotated[bool, typer.Option(
            '--clear-cache', help='Clears the script\'s cached files directory before running, with no confirmation.',
        )] = False,
    ) -> None:
    if debug:
        log_level = LogLevel.DEBUG
    init_logger(log_level, log_file)
    logger.debug('Logger initialized')

    if clear_cache:
        logger.info('Clearing the cache...')
        shutil.rmtree(FILE_CACHE.cache_dir)

if __name__ == '__main__':
    cli()
