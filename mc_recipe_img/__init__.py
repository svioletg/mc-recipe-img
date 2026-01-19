import sys
from collections.abc import Callable
from importlib.metadata import PackageMetadata, metadata
from pathlib import Path
from typing import Any

import platformdirs
from loguru import logger
from PIL import Image

type Point = tuple[int, int]

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

    def __repr__(self) -> str:
        return f'FileCache(cache_dir=\'{self.cache_dir}\', enabled={self.enabled})'

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

FILE_CACHE: FileCache = FileCache(USER_CACHE_DIR)

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

MEM_CACHE: MemoryCache = MemoryCache()

TEXTURE_CACHE: dict[str, Image.Image] = {}

def init_logger(
        stdout_level: str = 'INFO',
        fp: str | Path | None = None,
        *,
        fp_append: bool = False,
    ) -> tuple[int, int | None]:
    """
    Initializes (or re-initializes) the logger with a given level.

    :param fp: Optional file to save logs to.
    :param fp_append: If `True`, fp is opened in append mode rather than overwriting it.

    :returns (stdout_handler, file_handler?): The stdout handler ID and file handler ID, if `fp` is given.
    """
    logger.remove()

    logger.level('DEBUG', color='<fg #777777>')
    logger.level('INFO', color='<normal>')
    logger.level('WARNING', color='<yellow>')
    logger.level('ERROR', color='<red>')

    stdout_handler: int = logger.add(
        sys.stdout,
        colorize=True,
        format='<level>[{level}] {message}</level>',
        level=stdout_level,
        diagnose=False,
    )

    file_handler: int | None = None
    if fp:
        file_handler = logger.add(
            Path(fp),
            colorize=False,
            format='[{time:YYYY-MM-DD hh:mm:ss} {level}] {message}',
            level='DEBUG',
            diagnose=False,
            mode='a' if fp_append else 'w',
        )

    return stdout_handler, file_handler
