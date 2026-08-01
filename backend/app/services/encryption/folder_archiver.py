from __future__ import annotations

import os
import zipfile
from pathlib import Path


class ArchiveError(Exception):
    """Raised when a folder archive cannot be created or extracted."""


class FolderArchiver:
    """
    Creates and extracts ZIP archives of folder trees.

    Recursive traversal is implemented with streaming writes, so
    folders with many or large files can be archived without
    loading their content into memory.

    Security constraints:

    - Symlinks are skipped (never followed) to prevent archive
      traversal and dangling references.
    - Extraction rejects absolute paths, parent traversal and
      duplicate entries, making it safe against malicious archives.
    - Empty directories are preserved.
    """

    def create_archive(
        self,
        folder_path: str | Path,
        archive_path: str | Path | None = None,
        compression: int = zipfile.ZIP_DEFLATED,
    ) -> Path:
        """
        Recursively archive a folder.

        Args:
            folder_path: directory to archive.
            archive_path: optional destination archive path.
                Defaults to ``<folder>.zip`` beside the folder.
            compression: zipfile compression mode.

        Returns:
            The path of the created archive.

        Raises:
            ArchiveError: when the folder does not exist or the
                archive cannot be written.
        """

        folder = Path(folder_path)

        if not folder.is_dir():
            raise ArchiveError(
                f"Folder not found: {folder}"
            )

        archive = (
            Path(archive_path)
            if archive_path
            else folder.with_suffix(".zip")
        )

        archive.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:

            with zipfile.ZipFile(
                archive,
                "w",
                compression=compression,
                allowZip64=True,
            ) as zf:

                for file_path in self._walk(folder):

                    relative = file_path.relative_to(
                        folder
                    )

                    arcname = (
                        str(relative).replace(
                            os.sep,
                            "/"
                        )
                    )

                    if file_path.is_dir():

                        zf.writestr(
                            arcname + "/",
                            b"",
                        )

                    else:

                        zf.write(
                            file_path,
                            arcname=arcname,
                        )

            return archive

        except OSError as exc:
            raise ArchiveError(
                f"Failed to create archive: {exc}"
            ) from exc

    def extract_archive(
        self,
        archive_path: str | Path,
        destination: str | Path,
    ) -> Path:
        """
        Restore an archive into a destination directory.

        The folder structure stored inside the archive is
        reconstructed under ``destination``.

        Args:
            archive_path: ZIP archive to extract.
            destination: directory where files are restored.

        Returns:
            The destination directory.

        Raises:
            ArchiveError: when the archive is invalid, contains
                unsafe member names or cannot be extracted.
        """

        archive = Path(archive_path)

        if not archive.is_file():
            raise ArchiveError(
                f"Archive not found: {archive}"
            )

        destination_dir = Path(destination)

        destination_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:

            with zipfile.ZipFile(
                archive,
                "r",
            ) as zf:

                seen = set()

                for info in zf.infolist():

                    member = (
                        info.filename.replace(
                            "\\",
                            "/",
                        )
                    )

                    if (
                        member.startswith("/")
                        or ".." in member.split("/")
                    ):
                        raise ArchiveError(
                            f"Unsafe path in archive: {member}"
                        )

                    if member in seen:
                        raise ArchiveError(
                            f"Duplicate path in archive: {member}"
                        )

                    seen.add(member)

                    target = destination_dir.joinpath(
                        member
                    )

                    if member.endswith("/"):

                        target.mkdir(
                            parents=True,
                            exist_ok=True,
                        )

                        continue

                    target.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    with (
                        zf.open(info, "r") as source,
                        target.open("wb") as out,
                    ):

                        while True:

                            chunk = source.read(
                                1024 * 1024
                            )

                            if not chunk:
                                break

                            out.write(chunk)

            return destination_dir

        except zipfile.BadZipFile as exc:
            raise ArchiveError(
                f"Invalid archive: {exc}"
            ) from exc

        except OSError as exc:
            raise ArchiveError(
                f"Failed to extract archive: {exc}"
            ) from exc

    # -------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------

    @staticmethod
    def _walk(
        folder: Path,
    ):
        """
        Recursively yield directories (depth-first, parents before
        children) and files, skipping symlinks.
        """

        yield folder

        for child in sorted(
            folder.iterdir(),
            key=lambda p: p.name,
        ):

            if child.is_symlink():
                continue

            if child.is_dir():

                yield from FolderArchiver._walk(
                    child
                )

            elif child.is_file():

                yield child
