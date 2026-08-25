import os
import subprocess
from collections.abc import Iterable
from pathlib import Path

PROCESSING_DIR = [
    Path("/mnt/alpha/_jellyfin/catalog"),
]

MKV_FILES = "*.mkv"

JELLYFIN_UID = 970
JELLYFIN_GID = 970

DIR_PERMISSION = 0o775
FILE_PERMISSION = 0o664


def run_command(command: list[str]) -> None:
    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        check=True,
    )


def find_mkv_files(directories: Iterable[Path]) -> list[Path]:
    mkv_files: set[Path] = set()

    for directory in directories:
        if directory.is_dir():
            mkv_files.update(directory.rglob(MKV_FILES))

    return sorted(mkv_files)


def update_mkv_title(mkv_path: Path) -> str:
    updated_title = mkv_path.stem

    run_command(
        [
            "mkvpropedit",
            str(mkv_path),
            "--edit",
            "info",
            "--set",
            f"title={updated_title}",
        ]
    )

    return updated_title


def iter_media_paths(directories: Iterable[Path]) -> Iterable[Path]:
    seen_paths: set[Path] = set()

    for directory in directories:
        if not directory.is_dir():
            continue

        if directory not in seen_paths:
            seen_paths.add(directory)
            yield directory

        for path in directory.rglob("*"):
            if path not in seen_paths:
                seen_paths.add(path)
                yield path


def normalize_path(path: Path) -> None:
    mode = DIR_PERMISSION if path.is_dir() else FILE_PERMISSION
    path.chmod(mode)
    os.chown(path, JELLYFIN_UID, JELLYFIN_GID)


def normalize_permissions(directories: Iterable[Path]) -> None:
    for path in iter_media_paths(directories):
        normalize_path(path)


def main() -> None:
    updated_titles: set[str] = set()

    for mkv_file in find_mkv_files(PROCESSING_DIR):
        updated_title = update_mkv_title(mkv_file)
        if updated_title:
            updated_titles.add(updated_title)

    for title in sorted(updated_titles):
        print(title)

    normalize_permissions(PROCESSING_DIR)


if __name__ == "__main__":
    main()