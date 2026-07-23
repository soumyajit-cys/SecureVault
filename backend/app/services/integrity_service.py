from pathlib import Path

from app.crypto.hashing.sha256 import (
    SHA256Engine,
)


class IntegrityService:

    def __init__(
        self,
    ):
        self.engine = (
            SHA256Engine()
        )

    def checksum_text(
        self,
        text: str,
    ) -> str:

        return (
            self.engine.digest_text(
                text
            )
        )

    def checksum_bytes(
        self,
        data: bytes,
    ) -> str:

        return (
            self.engine.digest(
                data
            )
        )

    def checksum_file(
        self,
        file_path: str | Path,
    ) -> str:

        return (
            self.engine.digest_file(
                file_path
            )
        )

    def verify_text(
        self,
        text: str,
        expected_hash: str,
    ) -> bool:

        return (
            self.checksum_text(text)
            == expected_hash
        )

    def verify_file(
        self,
        file_path: str | Path,
        expected_hash: str,
    ) -> bool:

        return self.engine.verify_file(
            file_path,
            expected_hash,
        )