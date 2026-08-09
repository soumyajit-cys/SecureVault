from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.api.dependencies.current_user import (
    get_current_user,
)

from app.api.dependencies.storage import (
    get_crypto_service,
    get_key_management_service,
)

from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
)

from app.schemas.encryption import (
    DecryptTextRequest,
    DecryptTextResponse,
    EncryptTextRequest,
    EncryptTextResponse,
)

from app.services.crypto_service import (
    CryptoService,
)

from app.services.key_management_service import (
    KeyManagementService,
    KeyNotFoundError,
)

router = APIRouter(
    prefix="/encryption",
    tags=["Encryption"],
)


@router.post(
    "/text/encrypt",
    response_model=EncryptTextResponse,
)
def encrypt_text(
    payload: EncryptTextRequest,
    current_user=Depends(
        get_current_user
    ),
    crypto_service: CryptoService = Depends(
        get_crypto_service
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
):

    try:

        key = keys.get_active_key(
            current_user.id
        )

        encrypted = (
            crypto_service.encrypt_text(
                current_user.id,
                key,
                payload.plaintext,
                aad=payload.aad,
            )
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except EncryptionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return EncryptTextResponse(
        nonce=encrypted.nonce.decode(),
        ciphertext=encrypted.ciphertext.decode(),
        tag=encrypted.tag.decode(),
        encrypted_key=encrypted.encrypted_key.decode(),
        algorithm=encrypted.algorithm,
        key_algorithm=encrypted.key_algorithm,
        hash_algorithm=encrypted.hash_algorithm,
    )


@router.post(
    "/text/decrypt",
    response_model=DecryptTextResponse,
)
def decrypt_text(
    payload: DecryptTextRequest,
    current_user=Depends(
        get_current_user
    ),
    crypto_service: CryptoService = Depends(
        get_crypto_service
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
):

    from app.crypto.models.hybrid_payload import (
        HybridEncryptedPayload,
    )

    try:

        key = keys.get_active_key(
            current_user.id
        )

        hybrid = HybridEncryptedPayload(
            nonce=payload.nonce,
            ciphertext=payload.ciphertext,
            tag=payload.tag,
            encrypted_key=payload.encrypted_key,
        )

        plaintext = crypto_service.decrypt_text(
            current_user.id,
            key,
            hybrid,
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except DecryptionError as exc:
        raise HTTPException(
            status_code=422,
            detail="Decryption failed: invalid ciphertext.",
        ) from exc

    return DecryptTextResponse(
        plaintext=plaintext,
    )