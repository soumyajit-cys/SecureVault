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


class PwnedPasswordError(
    WeakPasswordError
):
    pass


class MfaRequiredError(
    AuthenticationError
):
    pass


class MfaVerificationFailedError(
    AuthenticationError
):
    pass


class PasswordResetTokenInvalidError(
    AuthenticationError
):
    pass


class EmailVerificationTokenInvalidError(
    AuthenticationError
):
    pass


class EmailNotVerifiedError(
    AuthenticationError
):
    pass


class QuotaExceededError(
    SecureVaultException
):
    pass


class LoginRateLimitedError(
    AuthenticationError
):
    pass