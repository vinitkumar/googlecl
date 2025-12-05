"""Gmail service implementation."""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Any

from google_cl.services.base import BaseService

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


log = logging.getLogger(__name__)


@dataclass
class Email:
    """Represents an email message."""

    id: str
    thread_id: str
    subject: str
    sender: str
    to: str
    date: str
    snippet: str
    body: str = ""
    labels: list[str] | None = None

    @classmethod
    def from_api_response(cls, msg: dict[str, Any]) -> "Email":
        """Create Email from Gmail API response."""
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        # Extract body
        body = ""
        payload = msg.get("payload", {})
        if "body" in payload and payload["body"].get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        elif "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="ignore"
                    )
                    break

        return cls(
            id=msg.get("id", ""),
            thread_id=msg.get("threadId", ""),
            subject=headers.get("Subject", "(No Subject)"),
            sender=headers.get("From", "Unknown"),
            to=headers.get("To", ""),
            date=headers.get("Date", ""),
            snippet=msg.get("snippet", ""),
            body=body,
            labels=msg.get("labelIds"),
        )


@dataclass
class Label:
    """Represents a Gmail label."""

    id: str
    name: str
    type: str
    messages_total: int = 0
    messages_unread: int = 0

    @classmethod
    def from_api_response(cls, label: dict[str, Any]) -> "Label":
        """Create Label from Gmail API response."""
        return cls(
            id=label.get("id", ""),
            name=label.get("name", ""),
            type=label.get("type", ""),
            messages_total=label.get("messagesTotal", 0),
            messages_unread=label.get("messagesUnread", 0),
        )


class GmailService(BaseService):
    """Service for interacting with Gmail API."""

    service_name = "gmail"
    service_version = "v1"

    def __init__(self, credentials: Credentials) -> None:
        """Initialize Gmail service."""
        super().__init__(credentials)
        self.user_id = "me"  # Special value for authenticated user

    def test_connection(self) -> bool:
        """Test the connection by getting user profile."""
        try:
            profile = self.service.users().getProfile(userId=self.user_id).execute()
            log.info("Connected to Gmail: %s", profile.get("emailAddress"))
            return True
        except Exception as e:
            log.error("Failed to connect to Gmail: %s", e)
            return False

    def get_profile(self) -> dict[str, Any]:
        """Get the authenticated user's Gmail profile."""
        return self.service.users().getProfile(userId=self.user_id).execute()

    def list_labels(self) -> list[Label]:
        """
        List all labels in the user's mailbox.

        Returns:
            List of Label objects.
        """
        response = self.service.users().labels().list(userId=self.user_id).execute()
        labels = response.get("labels", [])

        result = []
        for label in labels:
            # Get full label details
            try:
                full_label = (
                    self.service.users().labels().get(userId=self.user_id, id=label["id"]).execute()
                )
                result.append(Label.from_api_response(full_label))
            except Exception:
                result.append(Label.from_api_response(label))

        return result

    def list_messages(
        self,
        max_results: int = 10,
        label_ids: list[str] | None = None,
        query: str | None = None,
        include_spam_trash: bool = False,
    ) -> list[Email]:
        """
        List messages in the user's mailbox.

        Args:
            max_results: Maximum number of messages to return.
            label_ids: Only return messages with these labels.
            query: Gmail search query (same as web interface).
            include_spam_trash: Include spam and trash in results.

        Returns:
            List of Email objects.
        """
        kwargs: dict[str, Any] = {
            "userId": self.user_id,
            "maxResults": max_results,
            "includeSpamTrash": include_spam_trash,
        }

        if label_ids:
            kwargs["labelIds"] = label_ids
        if query:
            kwargs["q"] = query

        response = self.service.users().messages().list(**kwargs).execute()
        messages = response.get("messages", [])

        # Fetch full message details
        emails = []
        for msg in messages:
            full_msg = (
                self.service.users()
                .messages()
                .get(userId=self.user_id, id=msg["id"], format="full")
                .execute()
            )
            emails.append(Email.from_api_response(full_msg))

        return emails

    def get_message(self, message_id: str) -> Email:
        """
        Get a specific message by ID.

        Args:
            message_id: The ID of the message to retrieve.

        Returns:
            Email object with full message details.
        """
        msg = (
            self.service.users()
            .messages()
            .get(userId=self.user_id, id=message_id, format="full")
            .execute()
        )
        return Email.from_api_response(msg)

    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
    ) -> dict[str, Any]:
        """
        Send an email message.

        Args:
            to: Recipient email address.
            subject: Email subject.
            body: Email body content.
            html: If True, body is treated as HTML.

        Returns:
            API response with sent message details.
        """
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject

        if html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))

        # Encode the message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        return (
            self.service.users()
            .messages()
            .send(userId=self.user_id, body={"raw": raw})
            .execute()
        )

    def trash_message(self, message_id: str) -> dict[str, Any]:
        """
        Move a message to trash.

        Args:
            message_id: The ID of the message to trash.

        Returns:
            API response.
        """
        return (
            self.service.users()
            .messages()
            .trash(userId=self.user_id, id=message_id)
            .execute()
        )

    def untrash_message(self, message_id: str) -> dict[str, Any]:
        """
        Remove a message from trash.

        Args:
            message_id: The ID of the message to untrash.

        Returns:
            API response.
        """
        return (
            self.service.users()
            .messages()
            .untrash(userId=self.user_id, id=message_id)
            .execute()
        )

    def mark_as_read(self, message_id: str) -> dict[str, Any]:
        """Mark a message as read by removing UNREAD label."""
        return (
            self.service.users()
            .messages()
            .modify(userId=self.user_id, id=message_id, body={"removeLabelIds": ["UNREAD"]})
            .execute()
        )

    def mark_as_unread(self, message_id: str) -> dict[str, Any]:
        """Mark a message as unread by adding UNREAD label."""
        return (
            self.service.users()
            .messages()
            .modify(userId=self.user_id, id=message_id, body={"addLabelIds": ["UNREAD"]})
            .execute()
        )

    def search(self, query: str, max_results: int = 10) -> list[Email]:
        """
        Search for messages using Gmail query syntax.

        Args:
            query: Gmail search query (e.g., "from:user@example.com", "is:unread").
            max_results: Maximum number of results.

        Returns:
            List of matching Email objects.
        """
        return self.list_messages(max_results=max_results, query=query)

