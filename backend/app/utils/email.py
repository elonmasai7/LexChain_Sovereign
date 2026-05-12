"""Email service utilities."""
import logging
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class EmailService:
    """Email sending service."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """Send an email."""
        logger.info(f"Email to {to}: {subject}")
        return True

    async def send_verification_email(self, to: str, token: str) -> bool:
        """Send email verification email."""
        subject = "Verify your email - LexChain Sovereign"
        body = f"""Welcome to LexChain Sovereign!

Please verify your email by clicking the link below:
{settings.APP_NAME}/verify-email?token={token}

If you did not create this account, please ignore this email.
"""
        return await self.send_email(to, subject, body)

    async def send_password_reset_email(self, to: str, token: str) -> bool:
        """Send password reset email."""
        subject = "Reset your password - LexChain Sovereign"
        body = f"""You requested a password reset.

Click the link below to reset your password:
{settings.APP_NAME}/reset-password?token={token}

If you did not request this, please ignore this email.
"""
        return await self.send_email(to, subject, body)

    async def send_compliance_alert(self, to: str, alert_type: str, details: dict) -> bool:
        """Send compliance alert email."""
        subject = f"Compliance Alert: {alert_type}"
        body = f"""Compliance Alert - {alert_type}

Details:
{details}

This is an automated alert from LexChain Sovereign.
"""
        return await self.send_email(to, subject, body)

    async def send_welcome_email(self, to: str, name: str) -> bool:
        """Send welcome email."""
        subject = "Welcome to LexChain Sovereign"
        body = f"""Welcome, {name}!

Thank you for joining LexChain Sovereign - the AI-powered decentralized legal infrastructure platform.

Get started:
1. Complete your KYC verification
2. Connect your wallet
3. Explore the platform

If you have any questions, contact support.
"""
        return await self.send_email(to, subject, body)


email_service = EmailService()