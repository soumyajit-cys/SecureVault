import hashlib
from pathlib import Path

from app.crypto.interfaces.hash import HashEngine
from app.crypto.models.hash_result import HashResult


class SHA256Engine(HashEngine):

    CHUNK_SIZE = 1024 * 1024

    def digest(
        self,
        data: bytes,
    ) -> str:

        return hashlib.sha256(
            data
        ).hexdigest()

    def digest_text(
        self,
        text: str,
    ) -> str:

        return self.digest(
            text.encode()
        )

    def digest_file(
        self,
        file_path: str | Path,
    ) -> str:

        sha = hashlib.sha256()

        with open(
            file_path,
            "rb",
        ) as file:

            while chunk := file.read(
                self.CHUNK_SIZE
            ):
                sha.update(
                    chunk
                )

        return sha.hexdigest()

    def verify(
        self,
        data: bytes,
        expected_hash: str,
    ) -> bool:

        return (
            self.digest(data)
            == expected_hash
        )

    def verify_file(
        self,
        file_path: str | Path,
        expected_hash: str,
    ) -> bool:

        return (
            self.digest_file(
                file_path
            )
            == expected_hash
        )

    def result(
        self,
        data: bytes,
    ) -> HashResult:

        return HashResult(
            algorithm="SHA-256",
            digest=self.digest(data),
        )