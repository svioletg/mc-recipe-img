import sys
from collections.abc import Callable
from importlib.metadata import PackageMetadata, metadata
from pathlib import Path
from typing import Any

import platformdirs
from loguru import logger

PROJECT_NAME: str = 'mc_recipe_img'
SRC_ROOT: Path = Path(__file__).absolute().parent
PROJECT_META: PackageMetadata = metadata(PROJECT_NAME)
VERSION: str = PROJECT_META['version']

ASSETS_DIR: Path = SRC_ROOT / 'asset'

USER_CACHE_DIR: Path = Path(platformdirs.user_cache_dir(
    PROJECT_NAME,
    appauthor='Seth Violet Gibbs',
    ensure_exists=True,
))

DATAPACK_FORMAT_VERSIONS: dict[int | float, list[str]] = {
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
}

logger.remove()

class FileCache:
    def __init__(self, cache_dir: str | Path, *, enabled: bool = True) -> None:
        """
        :param cache_dir: The directory this cache will look for files in.
        :param enabled: If `False`, the cache will be disabled. More specifically, `FileCache.exists()` always returns
            `False`, `FileCache.get()` always returns its `default` parameter, and `FileCache.store()` writes nothing
            to disk (but still returns the `Path` it would have written to).
        """
        self.cache_dir = Path(cache_dir).absolute()
        if not self.cache_dir.is_dir():
            raise NotADirectoryError(f'Not a directory or does not exist: {self.cache_dir}')
        self.enabled = enabled

    def exists(self, fp: str | Path) -> bool:
        """Returns whether `fp` exists in this cache's directory."""
        if not self.enabled:
            return False

        return (self.cache_dir / fp).is_file()

    def get[T](self, fp: str | Path, default: T | None = None, *, parser: Callable[[str], T] = str) -> T | None:
        """
        Returns the contents of the file at `fp` in this cache's directory if the path exists, otherwise returns
        `None`. The file contents are decoded with UTF-8 and passed to `parser` before returning them—`parser` is *not*
        called on `default`.
        """
        if not self.enabled:
            return default

        if (fp := self.cache_dir / fp).is_file():
            return parser(fp.read_text('utf-8'))
        return default

    def store(self, fp: str | Path, value: str) -> Path:
        """
        Stores the contents of `value` to `fp` in this cache's directory, creating the file if it does not exist or
        overwriting the existing file, and returns the absolute path to this file.
        The contents are stored in UTF-8 encoding.
        """
        fp = self.cache_dir / fp
        if not self.enabled:
            return fp

        if fp.parent != self.cache_dir:
            fp.parent.mkdir(parents=True, exist_ok=True)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(value)
        return fp

file_cache: FileCache = FileCache(USER_CACHE_DIR)

class MemoryCache:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def get_or_store[T](self, key: str, store_callback: Callable[[], T]) -> T:
        """
        Retrieves the value of `key` from the cache if one exists, otherwise calls `store_callback` and stores the
        result to this key, and returns that same value.
        """
        if key in self.data:
            return self.data[key]
        value: T = store_callback()
        self.data[key] = value
        return value

mem_cache: MemoryCache = MemoryCache()

def init_logger(stdout_level: str = 'INFO') -> int:
    """
    Initializes (or re-initializes) the logger with a given level.

    :returns stdout_handler: `int`
    """
    logger.remove()

    logger.level('DEBUG', color='<blue>')
    logger.level('INFO', color='<fg #ffffff>')
    logger.level('WARNING', color='<yellow>')
    logger.level('ERROR', color='<red>')

    return logger.add(
        sys.stdout,
        colorize=True,
        format='<level>[{level}] {message}</level>',
        level=stdout_level,
        diagnose=False,
    )
