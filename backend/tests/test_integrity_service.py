from app.services.integrity_service import (
    IntegrityService,
)


def test_integrity_service():

    service = (
        IntegrityService()
    )

    digest = (
        service.checksum_text(
            "SecureVault"
        )
    )

    assert (
        service.verify_text(
            "SecureVault",
            digest,
        )
        is True
    )