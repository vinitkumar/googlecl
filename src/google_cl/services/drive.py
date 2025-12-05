"""Google Drive service implementation."""

from __future__ import annotations

import io
import logging
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from google_cl.services.base import BaseService

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


log = logging.getLogger(__name__)


# Common MIME type mappings for Google Workspace files
GOOGLE_MIME_TYPES = {
    "application/vnd.google-apps.document": "Google Docs",
    "application/vnd.google-apps.spreadsheet": "Google Sheets",
    "application/vnd.google-apps.presentation": "Google Slides",
    "application/vnd.google-apps.folder": "Folder",
    "application/vnd.google-apps.form": "Google Form",
    "application/vnd.google-apps.drawing": "Google Drawing",
}

# Export formats for Google Workspace files
EXPORT_FORMATS = {
    "application/vnd.google-apps.document": {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "html": "text/html",
    },
    "application/vnd.google-apps.spreadsheet": {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
    },
    "application/vnd.google-apps.presentation": {
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
}


@dataclass
class DriveFile:
    """Represents a file in Google Drive."""

    id: str
    name: str
    mime_type: str
    size: int | None
    created_time: str
    modified_time: str
    parents: list[str] | None
    web_view_link: str | None
    is_folder: bool

    @classmethod
    def from_api_response(cls, file: dict[str, Any]) -> "DriveFile":
        """Create DriveFile from Drive API response."""
        mime_type = file.get("mimeType", "")
        return cls(
            id=file.get("id", ""),
            name=file.get("name", ""),
            mime_type=mime_type,
            size=int(file["size"]) if "size" in file else None,
            created_time=file.get("createdTime", ""),
            modified_time=file.get("modifiedTime", ""),
            parents=file.get("parents"),
            web_view_link=file.get("webViewLink"),
            is_folder=mime_type == "application/vnd.google-apps.folder",
        )

    @property
    def type_name(self) -> str:
        """Get human-readable type name."""
        if self.mime_type in GOOGLE_MIME_TYPES:
            return GOOGLE_MIME_TYPES[self.mime_type]
        return self.mime_type.split("/")[-1].upper() if self.mime_type else "Unknown"

    @property
    def size_formatted(self) -> str:
        """Get formatted file size."""
        if self.size is None:
            return "-"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if self.size < 1024:
                return f"{self.size:.1f} {unit}"
            self.size //= 1024
        return f"{self.size:.1f} PB"


class DriveService(BaseService):
    """Service for interacting with Google Drive API."""

    service_name = "drive"
    service_version = "v3"

    def __init__(self, credentials: Credentials) -> None:
        """Initialize Drive service."""
        super().__init__(credentials)

    def test_connection(self) -> bool:
        """Test the connection by getting storage quota."""
        try:
            about = self.service.about().get(fields="user,storageQuota").execute()
            user = about.get("user", {})
            log.info("Connected to Drive: %s", user.get("emailAddress"))
            return True
        except Exception as e:
            log.error("Failed to connect to Drive: %s", e)
            return False

    def get_storage_quota(self) -> dict[str, Any]:
        """Get storage quota information."""
        about = self.service.about().get(fields="storageQuota").execute()
        return about.get("storageQuota", {})

    def list_files(
        self,
        max_results: int = 20,
        folder_id: str | None = None,
        query: str | None = None,
        order_by: str = "modifiedTime desc",
        include_trashed: bool = False,
    ) -> list[DriveFile]:
        """
        List files in Google Drive.

        Args:
            max_results: Maximum number of files to return.
            folder_id: Only list files in this folder.
            query: Additional Drive API query string.
            order_by: Field to sort by.
            include_trashed: Include trashed files.

        Returns:
            List of DriveFile objects.
        """
        # Build query
        queries = []
        if not include_trashed:
            queries.append("trashed = false")
        if folder_id:
            queries.append(f"'{folder_id}' in parents")
        if query:
            queries.append(query)

        q = " and ".join(queries) if queries else None

        response = (
            self.service.files()
            .list(
                pageSize=max_results,
                q=q,
                orderBy=order_by,
                fields="files(id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink)",
            )
            .execute()
        )

        return [DriveFile.from_api_response(f) for f in response.get("files", [])]

    def get_file(self, file_id: str) -> DriveFile:
        """
        Get details about a specific file.

        Args:
            file_id: The ID of the file.

        Returns:
            DriveFile object.
        """
        file = (
            self.service.files()
            .get(
                fileId=file_id,
                fields="id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink",
            )
            .execute()
        )
        return DriveFile.from_api_response(file)

    def search_files(
        self,
        name: str | None = None,
        mime_type: str | None = None,
        full_text: str | None = None,
        max_results: int = 20,
    ) -> list[DriveFile]:
        """
        Search for files in Drive.

        Args:
            name: Search by file name (contains).
            mime_type: Filter by MIME type.
            full_text: Full-text search in file content.
            max_results: Maximum number of results.

        Returns:
            List of matching DriveFile objects.
        """
        queries = ["trashed = false"]

        if name:
            queries.append(f"name contains '{name}'")
        if mime_type:
            queries.append(f"mimeType = '{mime_type}'")
        if full_text:
            queries.append(f"fullText contains '{full_text}'")

        return self.list_files(max_results=max_results, query=" and ".join(queries))

    def download_file(self, file_id: str, destination: Path) -> Path:
        """
        Download a file from Drive.

        Args:
            file_id: The ID of the file to download.
            destination: Local path to save the file.

        Returns:
            Path to the downloaded file.
        """
        # Get file info first
        file_info = self.get_file(file_id)

        # Handle Google Workspace files (need export)
        if file_info.mime_type.startswith("application/vnd.google-apps"):
            return self._export_file(file_id, file_info.mime_type, destination)

        # Regular file download
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            log.debug("Download progress: %d%%", int(status.progress() * 100))

        destination.write_bytes(fh.getvalue())
        log.info("Downloaded %s to %s", file_info.name, destination)
        return destination

    def _export_file(self, file_id: str, mime_type: str, destination: Path) -> Path:
        """Export a Google Workspace file to a downloadable format."""
        # Determine export format
        export_formats = EXPORT_FORMATS.get(mime_type, {})
        if not export_formats:
            raise ValueError(f"Cannot export files of type: {mime_type}")

        # Default to PDF if available
        export_mime = export_formats.get("pdf", list(export_formats.values())[0])

        request = self.service.files().export_media(fileId=file_id, mimeType=export_mime)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        destination.write_bytes(fh.getvalue())
        log.info("Exported file to %s", destination)
        return destination

    def upload_file(
        self,
        file_path: Path,
        name: str | None = None,
        folder_id: str | None = None,
        mime_type: str | None = None,
    ) -> DriveFile:
        """
        Upload a file to Google Drive.

        Args:
            file_path: Local file path to upload.
            name: Name for the file in Drive (defaults to local filename).
            folder_id: Parent folder ID.
            mime_type: MIME type (auto-detected if not provided).

        Returns:
            DriveFile object for the uploaded file.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if name is None:
            name = file_path.name

        if mime_type is None:
            mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

        file_metadata: dict[str, Any] = {"name": name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

        file = (
            self.service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink",
            )
            .execute()
        )

        log.info("Uploaded %s to Drive", name)
        return DriveFile.from_api_response(file)

    def create_folder(self, name: str, parent_id: str | None = None) -> DriveFile:
        """
        Create a folder in Google Drive.

        Args:
            name: Name of the folder.
            parent_id: Parent folder ID.

        Returns:
            DriveFile object for the created folder.
        """
        file_metadata: dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        folder = (
            self.service.files()
            .create(
                body=file_metadata,
                fields="id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink",
            )
            .execute()
        )

        log.info("Created folder: %s", name)
        return DriveFile.from_api_response(folder)

    def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """
        Delete a file (move to trash or permanently delete).

        Args:
            file_id: The ID of the file to delete.
            permanent: If True, permanently delete. Otherwise move to trash.

        Returns:
            True if successful.
        """
        if permanent:
            self.service.files().delete(fileId=file_id).execute()
            log.info("Permanently deleted file: %s", file_id)
        else:
            self.service.files().update(fileId=file_id, body={"trashed": True}).execute()
            log.info("Moved file to trash: %s", file_id)
        return True

    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = "reader",
        send_notification: bool = True,
    ) -> dict[str, Any]:
        """
        Share a file with a user.

        Args:
            file_id: The ID of the file to share.
            email: Email address of the user to share with.
            role: Permission role ('reader', 'writer', 'commenter').
            send_notification: Whether to send email notification.

        Returns:
            Permission object.
        """
        permission = {"type": "user", "role": role, "emailAddress": email}

        return (
            self.service.permissions()
            .create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=send_notification,
            )
            .execute()
        )

