"""Google Calendar service implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from google_cl.services.base import BaseService

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


log = logging.getLogger(__name__)


@dataclass
class Calendar:
    """Represents a Google Calendar."""

    id: str
    summary: str
    description: str
    time_zone: str
    is_primary: bool
    background_color: str
    foreground_color: str

    @classmethod
    def from_api_response(cls, cal: dict[str, Any]) -> Calendar:
        """Create Calendar from API response."""
        return cls(
            id=cal.get("id", ""),
            summary=cal.get("summary", ""),
            description=cal.get("description", ""),
            time_zone=cal.get("timeZone", ""),
            is_primary=cal.get("primary", False),
            background_color=cal.get("backgroundColor", ""),
            foreground_color=cal.get("foregroundColor", ""),
        )


@dataclass
class Event:
    """Represents a calendar event."""

    id: str
    summary: str
    description: str
    location: str
    start: datetime | str
    end: datetime | str
    all_day: bool
    status: str
    html_link: str
    creator: str
    attendees: list[dict[str, Any]] = field(default_factory=list)
    recurrence: list[str] | None = None

    @classmethod
    def from_api_response(cls, event: dict[str, Any]) -> Event:
        """Create Event from API response."""
        # Handle start time (can be date or dateTime)
        start_data = event.get("start", {})
        if "dateTime" in start_data:
            start = start_data["dateTime"]
            all_day = False
        else:
            start = start_data.get("date", "")
            all_day = True

        # Handle end time
        end_data = event.get("end", {})
        end = end_data["dateTime"] if "dateTime" in end_data else end_data.get("date", "")

        creator = event.get("creator", {})

        return cls(
            id=event.get("id", ""),
            summary=event.get("summary", "(No title)"),
            description=event.get("description", ""),
            location=event.get("location", ""),
            start=start,
            end=end,
            all_day=all_day,
            status=event.get("status", ""),
            html_link=event.get("htmlLink", ""),
            creator=creator.get("email", ""),
            attendees=event.get("attendees", []),
            recurrence=event.get("recurrence"),
        )


class CalendarService(BaseService):
    """Service for interacting with Google Calendar API."""

    service_name = "calendar"
    service_version = "v3"

    def __init__(self, credentials: Credentials) -> None:
        """Initialize Calendar service."""
        super().__init__(credentials)

    def test_connection(self) -> bool:
        """Test the connection by listing calendars."""
        try:
            calendars = self.service.calendarList().list().execute()
            log.info("Connected to Calendar: %d calendars found", len(calendars.get("items", [])))
            return True
        except Exception as e:
            log.error("Failed to connect to Calendar: %s", e)
            return False

    def list_calendars(self) -> list[Calendar]:
        """
        List all calendars the user has access to.

        Returns:
            List of Calendar objects.
        """
        response = self.service.calendarList().list().execute()
        return [Calendar.from_api_response(cal) for cal in response.get("items", [])]

    def get_primary_calendar(self) -> Calendar | None:
        """Get the user's primary calendar."""
        calendars = self.list_calendars()
        for cal in calendars:
            if cal.is_primary:
                return cal
        return calendars[0] if calendars else None

    def list_events(
        self,
        calendar_id: str = "primary",
        max_results: int = 10,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        query: str | None = None,
        single_events: bool = True,
        order_by: str = "startTime",
    ) -> list[Event]:
        """
        List events from a calendar.

        Args:
            calendar_id: Calendar ID ('primary' for the main calendar).
            max_results: Maximum number of events to return.
            time_min: Start of time range (defaults to now).
            time_max: End of time range.
            query: Free text search query.
            single_events: Expand recurring events into instances.
            order_by: Order by 'startTime' or 'updated'.

        Returns:
            List of Event objects.
        """
        if time_min is None:
            time_min = datetime.utcnow()

        kwargs: dict[str, Any] = {
            "calendarId": calendar_id,
            "maxResults": max_results,
            "timeMin": time_min.isoformat() + "Z",
            "singleEvents": single_events,
            "orderBy": order_by,
        }

        if time_max:
            kwargs["timeMax"] = time_max.isoformat() + "Z"
        if query:
            kwargs["q"] = query

        response = self.service.events().list(**kwargs).execute()
        return [Event.from_api_response(event) for event in response.get("items", [])]

    def get_event(self, event_id: str, calendar_id: str = "primary") -> Event:
        """
        Get a specific event.

        Args:
            event_id: The ID of the event.
            calendar_id: Calendar ID.

        Returns:
            Event object.
        """
        event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return Event.from_api_response(event)

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime | None = None,
        description: str = "",
        location: str = "",
        calendar_id: str = "primary",
        attendees: list[str] | None = None,
        all_day: bool = False,
        timezone: str | None = None,
    ) -> Event:
        """
        Create a new calendar event.

        Args:
            summary: Event title.
            start: Start time.
            end: End time (defaults to 1 hour after start).
            description: Event description.
            location: Event location.
            calendar_id: Calendar ID.
            attendees: List of email addresses.
            all_day: Create an all-day event.
            timezone: Timezone for the event.

        Returns:
            Created Event object.
        """
        if end is None:
            end = start + timedelta(hours=1)

        event_body: dict[str, Any] = {
            "summary": summary,
            "description": description,
            "location": location,
        }

        if all_day:
            event_body["start"] = {"date": start.strftime("%Y-%m-%d")}
            event_body["end"] = {"date": end.strftime("%Y-%m-%d")}
        else:
            event_body["start"] = {"dateTime": start.isoformat()}
            event_body["end"] = {"dateTime": end.isoformat()}
            if timezone:
                event_body["start"]["timeZone"] = timezone
                event_body["end"]["timeZone"] = timezone

        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        created = (
            self.service.events().insert(calendarId=calendar_id, body=event_body).execute()
        )

        log.info("Created event: %s", summary)
        return Event.from_api_response(created)

    def quick_add(self, text: str, calendar_id: str = "primary") -> Event:
        """
        Create an event from natural language text.

        Args:
            text: Natural language description (e.g., "Meeting tomorrow at 3pm").
            calendar_id: Calendar ID.

        Returns:
            Created Event object.
        """
        created = (
            self.service.events().quickAdd(calendarId=calendar_id, text=text).execute()
        )
        log.info("Quick added event: %s", text)
        return Event.from_api_response(created)

    def update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: str | None = None,
        description: str | None = None,
        location: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Event:
        """
        Update an existing event.

        Args:
            event_id: The ID of the event to update.
            calendar_id: Calendar ID.
            summary: New title (if changing).
            description: New description (if changing).
            location: New location (if changing).
            start: New start time (if changing).
            end: New end time (if changing).

        Returns:
            Updated Event object.
        """
        # Get existing event
        event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Update fields
        if summary is not None:
            event["summary"] = summary
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location
        if start is not None:
            if "date" in event.get("start", {}):
                event["start"] = {"date": start.strftime("%Y-%m-%d")}
            else:
                event["start"] = {"dateTime": start.isoformat()}
        if end is not None:
            if "date" in event.get("end", {}):
                event["end"] = {"date": end.strftime("%Y-%m-%d")}
            else:
                event["end"] = {"dateTime": end.isoformat()}

        updated = (
            self.service.events()
            .update(calendarId=calendar_id, eventId=event_id, body=event)
            .execute()
        )

        log.info("Updated event: %s", event_id)
        return Event.from_api_response(updated)

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """
        Delete an event.

        Args:
            event_id: The ID of the event to delete.
            calendar_id: Calendar ID.

        Returns:
            True if successful.
        """
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        log.info("Deleted event: %s", event_id)
        return True

    def get_upcoming_events(
        self,
        days: int = 7,
        calendar_id: str = "primary",
        max_results: int = 20,
    ) -> list[Event]:
        """
        Get upcoming events for the next N days.

        Args:
            days: Number of days to look ahead.
            calendar_id: Calendar ID.
            max_results: Maximum number of events.

        Returns:
            List of upcoming Event objects.
        """
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days)
        return self.list_events(
            calendar_id=calendar_id,
            max_results=max_results,
            time_min=time_min,
            time_max=time_max,
        )

    def get_today_events(self, calendar_id: str = "primary") -> list[Event]:
        """
        Get all events for today.

        Args:
            calendar_id: Calendar ID.

        Returns:
            List of today's Event objects.
        """
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return self.list_events(
            calendar_id=calendar_id,
            time_min=start_of_day,
            time_max=end_of_day,
            max_results=50,
        )

