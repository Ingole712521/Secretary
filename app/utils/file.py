"""File system utilities."""

from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path) -> Path:
    """Create a directory and parents if they do not exist.

    Args:
        path: Directory path to ensure.

    Returns:
        The same path, guaranteed to exist.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text_file(path: Path, *, encoding: str = "utf-8") -> str:
    """Read the full contents of a text file.

    Args:
        path: File path to read.
        encoding: Text encoding.

    Returns:
        File contents as a string.
    """
    return path.read_text(encoding=encoding)


def write_text_file(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write text content to a file, creating parent directories as needed.

    Args:
        path: Destination file path.
        content: Text to write.
        encoding: Text encoding.
    """
    ensure_directory(path.parent)
    path.write_text(content, encoding=encoding)
