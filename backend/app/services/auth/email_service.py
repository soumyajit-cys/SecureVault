import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class EmailMessagePayload:
    to: str
    subject: str
    body: str


class EmailService:
    """
    Email delivery abstraction.

    EMAIL_BACKEND=console -> logs the message via structlog.
    EMAIL_BACKEND=smtp   -> sends over SMTP (TLS).
    """

    def __init__(self) -> None:
        self.backend = (
            settings.EMAIL_BACKEND or "console"
        )

    def send(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> bool:

        message = EmailMessagePayload(
            to=to,
            subject=subject,
            body=body,
        )

        if self.backend == "smtp":
            return self._send_smtp(message)

        return self._send_console(message)

    def _send_console(
        self,
        message: EmailMessagePayload,
    ) -> bool:

        logger.info(
            "email_queued",
            to=message.to,
            subject=message.subject,
            backend="console",
        )

        logger.info(
            "email_body",
            to=message.to,
            body=message.body,
        )

        return True

    def _send_smtp(
        self,
        message: EmailMessagePayload,
    ) -> bool:

        if not settings.SMTP_HOST:
            raise RuntimeError(
                "SMTP_HOST is not configured"
            )

        email = EmailMessage()

        email["Subject"] = (
            message.subject
        )

        email["From"] = (
            settings.SMTP_FROM
            or settings.SMTP_USERNAME
            or "SecureVault <no-reply@localhost>"
        )

        email["To"] = message.to

        email.set_content(
            message.body
        )

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=10,
        ) as server:

            if settings.SMTP_USE_TLS:
                server.starttls()

            if (
                settings.SMTP_USERNAME
                and settings.SMTP_PASSWORD
            ):
                server.login(
                    settings.SMTP_USERNAME,
                    settings.SMTP_PASSWORD,
                )

            server.send_message(
                email
            )

        return True
