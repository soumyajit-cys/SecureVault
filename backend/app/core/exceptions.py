class SecureVaultException(Exception):
    pass


class AuthenticationError(SecureVaultException):
    pass


class AuthorizationError(SecureVaultException):
    pass


class InvalidCredentialsError(AuthenticationError):
    pass


class AccountLockedError(AuthenticationError):
    pass


class UserAlreadyExistsError(AuthenticationError):
    pass


class TokenExpiredError(AuthenticationError):
    pass


class InvalidTokenError(AuthenticationError):
    pass


class ConflictError(SecureVaultException):
    pass


class UserAlreadyExistsError(ConflictError):
    pass


class NotFoundError(SecureVaultException):
    pass


class FileTooLargeError(SecureVaultException):
    pass


class WeakPasswordError(
    AuthenticationError
):
    pass