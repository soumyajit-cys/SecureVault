from pydantic import BaseModel


class PasswordValidationResult(
    BaseModel
):
    valid: bool
    message: str


    