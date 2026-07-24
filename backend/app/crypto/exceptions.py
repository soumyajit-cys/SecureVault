class CryptoException(Exception):
    pass


class EncryptionError(CryptoException):
    pass


class DecryptionError(CryptoException):
    pass


class InvalidKeyError(CryptoException):
    pass


class IntegrityVerificationError(
    CryptoException
):
    pass


