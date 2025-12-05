"""Base service class for Google API services."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import Resource


log = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all Google API services."""

    service_name: str = ""
    service_version: str = ""

    def __init__(self, credentials: Credentials) -> None:
        """
        Initialize the service with credentials.

        Args:
            credentials: Valid Google OAuth credentials.
        """
        self.credentials = credentials
        self._service: Resource | None = None

    @property
    def service(self) -> Resource:
        """Get or create the service client."""
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def _build_service(self) -> Resource:
        """Build the Google API service client."""
        from googleapiclient.discovery import build

        log.debug("Building %s service (v%s)", self.service_name, self.service_version)
        return build(
            self.service_name,
            self.service_version,
            credentials=self.credentials,
        )

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the service."""
        pass

    def _handle_error(self, error: Exception, operation: str) -> None:
        """Handle API errors with consistent logging."""
        log.error("Error during %s: %s", operation, error)
        raise

    def _paginate(
        self,
        request: Any,
        items_key: str,
        max_results: int | None = None,
    ) -> list[Any]:
        """
        Helper to paginate through API results.

        Args:
            request: Initial API request object.
            items_key: Key in response containing items.
            max_results: Maximum number of results to return.

        Returns:
            List of all items from paginated results.
        """
        all_items: list[Any] = []

        while request is not None:
            response = request.execute()
            items = response.get(items_key, [])
            all_items.extend(items)

            if max_results and len(all_items) >= max_results:
                return all_items[:max_results]

            request = self.service.list_next(request, response)

        return all_items

