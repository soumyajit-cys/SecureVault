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


class PermissionDeniedError(AuthorizationError):
    pass

class WeakPasswordError(
    AuthenticationError
):
    pass