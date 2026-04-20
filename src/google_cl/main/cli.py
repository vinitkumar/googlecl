"""
Command-line interface for GoogleCL.

This module provides a modern CLI using Typer for interacting with
Google services (Gmail, Drive, Calendar) from the command line.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from google_cl.main.auth import (
    DEFAULT_CREDENTIALS_FILE,
    DEFAULT_TOKEN_FILE,
    SCOPES,
    GoogleAuth,
)

# Initialize the main CLI app
app = typer.Typer(
    name="googlecl",
    help="🔍 Command-line interface for Google services",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Sub-apps for each service
gmail_app = typer.Typer(help="📧 Gmail operations", no_args_is_help=True)
drive_app = typer.Typer(help="📁 Google Drive operations", no_args_is_help=True)
calendar_app = typer.Typer(help="📅 Google Calendar operations", no_args_is_help=True)
auth_app = typer.Typer(help="🔐 Authentication management", no_args_is_help=True)

# Register sub-apps
app.add_typer(gmail_app, name="gmail")
app.add_typer(drive_app, name="drive")
app.add_typer(calendar_app, name="calendar")
app.add_typer(auth_app, name="auth")

# Console for rich output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)


def get_credentials(service: str | None = None) -> GoogleAuth:
    """Get authenticated credentials."""
    scopes = None
    if service and service in SCOPES:
        scopes = SCOPES[service]

    auth = GoogleAuth(scopes=scopes)
    auth.authenticate()
    return auth


# ============================================================================
# Authentication Commands
# ============================================================================


@auth_app.command("login")
def auth_login(
    force: Annotated[bool, typer.Option("--force", "-f", help="Force re-authentication")] = False,
) -> None:
    """Authenticate with Google services."""
    try:
        auth = GoogleAuth()
        auth.authenticate(force_new=force)
        rprint("[green]✓ Successfully authenticated![/green]")
    except FileNotFoundError as e:
        rprint(f"[red]✗ {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        rprint(f"[red]✗ Authentication failed: {e}[/red]")
        raise typer.Exit(1) from None


@auth_app.command("logout")
def auth_logout() -> None:
    """Remove stored authentication tokens."""
    auth = GoogleAuth()
    if auth.revoke():
        rprint("[green]✓ Successfully logged out![/green]")
    else:
        rprint("[yellow]No authentication tokens found.[/yellow]")


@auth_app.command("status")
def auth_status() -> None:
    """Check authentication status."""
    auth = GoogleAuth()
    if auth.is_authenticated():
        rprint("[green]✓ You are authenticated[/green]")
        rprint(f"  Token file: {DEFAULT_TOKEN_FILE}")
    else:
        rprint("[yellow]✗ Not authenticated[/yellow]")
        rprint("  Run [bold]googlecl auth login[/bold] to authenticate")


@auth_app.command("info")
def auth_info() -> None:
    """Show configuration paths and setup instructions."""
    table = Table(title="GoogleCL Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Config Directory", str(DEFAULT_CREDENTIALS_FILE.parent))
    table.add_row("Credentials File", str(DEFAULT_CREDENTIALS_FILE))
    table.add_row("Token File", str(DEFAULT_TOKEN_FILE))

    console.print(table)

    rprint("\n[bold]Setup Instructions:[/bold]")
    rprint("1. Go to https://console.cloud.google.com/")
    rprint("2. Create a new project or select existing")
    rprint("3. Enable the APIs: Gmail, Drive, Calendar")
    rprint("4. Go to APIs & Services > Credentials")
    rprint("5. Create OAuth 2.0 Client ID (Desktop application)")
    rprint(f"6. Download JSON and save to: [cyan]{DEFAULT_CREDENTIALS_FILE}[/cyan]")
    rprint("7. Run [bold]googlecl auth login[/bold]")


# ============================================================================
# Gmail Commands
# ============================================================================


@gmail_app.command("inbox")
def gmail_inbox(
    count: Annotated[int, typer.Option("--count", "-n", help="Number of emails to show")] = 10,
    unread: Annotated[bool, typer.Option("--unread", "-u", help="Show only unread emails")] = False,
) -> None:
    """List emails in your inbox."""
    from google_cl.services.gmail import GmailService

    try:
        auth = get_credentials("gmail")
        gmail = GmailService(auth.credentials)

        label_ids = ["INBOX"]
        if unread:
            label_ids.append("UNREAD")

        emails = gmail.list_messages(max_results=count, label_ids=label_ids)

        if not emails:
            rprint("[yellow]No emails found.[/yellow]")
            return

        table = Table(title=f"📧 Inbox ({len(emails)} messages)")
        table.add_column("From", style="cyan", max_width=30)
        table.add_column("Subject", style="white", max_width=50)
        table.add_column("Date", style="dim")
        table.add_column("ID", style="dim", max_width=15)

        for email in emails:
            # Truncate sender for display
            sender = email.sender[:30] + "..." if len(email.sender) > 30 else email.sender
            subject = email.subject[:50] + "..." if len(email.subject) > 50 else email.subject

            table.add_row(sender, subject, email.date[:20], email.id[:15])

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@gmail_app.command("read")
def gmail_read(
    message_id: Annotated[str, typer.Argument(help="Email message ID to read")],
) -> None:
    """Read a specific email."""
    from google_cl.services.gmail import GmailService

    try:
        auth = get_credentials("gmail")
        gmail = GmailService(auth.credentials)

        email = gmail.get_message(message_id)

        # Create a styled panel for the email
        content = Text()
        content.append("From: ", style="bold cyan")
        content.append(f"{email.sender}\n")
        content.append("To: ", style="bold cyan")
        content.append(f"{email.to}\n")
        content.append("Date: ", style="bold cyan")
        content.append(f"{email.date}\n")
        content.append("Subject: ", style="bold cyan")
        content.append(f"{email.subject}\n\n")
        content.append(email.body or email.snippet)

        panel = Panel(content, title="📧 Email", border_style="blue")
        console.print(panel)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@gmail_app.command("send")
def gmail_send(
    to: Annotated[str, typer.Option("--to", "-t", help="Recipient email address")],
    subject: Annotated[str, typer.Option("--subject", "-s", help="Email subject")],
    body: Annotated[str, typer.Option("--body", "-b", help="Email body")] = "",
    html: Annotated[bool, typer.Option("--html", help="Send as HTML")] = False,
) -> None:
    """Send an email."""
    from google_cl.services.gmail import GmailService

    try:
        auth = get_credentials("gmail")
        gmail = GmailService(auth.credentials)

        result = gmail.send_message(to=to, subject=subject, body=body, html=html)
        rprint("[green]✓ Email sent successfully![/green]")
        rprint(f"  Message ID: {result.get('id')}")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@gmail_app.command("search")
def gmail_search(
    query: Annotated[str, typer.Argument(help="Gmail search query")],
    count: Annotated[int, typer.Option("--count", "-n", help="Number of results")] = 10,
) -> None:
    """Search emails using Gmail query syntax."""
    from google_cl.services.gmail import GmailService

    try:
        auth = get_credentials("gmail")
        gmail = GmailService(auth.credentials)

        emails = gmail.search(query=query, max_results=count)

        if not emails:
            rprint("[yellow]No emails found matching your query.[/yellow]")
            return

        table = Table(title=f"🔍 Search Results for '{query}'")
        table.add_column("From", style="cyan", max_width=30)
        table.add_column("Subject", style="white", max_width=50)
        table.add_column("Date", style="dim")
        table.add_column("ID", style="dim", max_width=15)

        for email in emails:
            sender = email.sender[:30] + "..." if len(email.sender) > 30 else email.sender
            subject = email.subject[:50] + "..." if len(email.subject) > 50 else email.subject
            table.add_row(sender, subject, email.date[:20], email.id[:15])

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@gmail_app.command("labels")
def gmail_labels() -> None:
    """List all Gmail labels."""
    from google_cl.services.gmail import GmailService

    try:
        auth = get_credentials("gmail")
        gmail = GmailService(auth.credentials)

        labels = gmail.list_labels()

        table = Table(title="📑 Gmail Labels")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Messages", justify="right")
        table.add_column("Unread", justify="right", style="yellow")

        for label in labels:
            table.add_row(
                label.name,
                label.type,
                str(label.messages_total),
                str(label.messages_unread),
            )

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


# ============================================================================
# Drive Commands
# ============================================================================


@drive_app.command("list")
def drive_list(
    count: Annotated[int, typer.Option("--count", "-n", help="Number of files to show")] = 20,
    folder: Annotated[str | None, typer.Option("--folder", "-f", help="Folder ID")] = None,
) -> None:
    """List files in Google Drive."""
    from google_cl.services.drive import DriveService

    try:
        auth = get_credentials("drive")
        drive = DriveService(auth.credentials)

        files = drive.list_files(max_results=count, folder_id=folder)

        if not files:
            rprint("[yellow]No files found.[/yellow]")
            return

        table = Table(title="📁 Google Drive Files")
        table.add_column("Name", style="cyan", max_width=40)
        table.add_column("Type", style="dim", max_width=15)
        table.add_column("Size", justify="right")
        table.add_column("Modified", style="dim")
        table.add_column("ID", style="dim", max_width=20)

        for f in files:
            icon = "📁" if f.is_folder else "📄"
            name = f"{icon} {f.name}"
            if len(name) > 40:
                name = name[:37] + "..."
            table.add_row(
                name,
                f.type_name[:15],
                f.size_formatted,
                f.modified_time[:10],
                f.id[:20],
            )

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@drive_app.command("search")
def drive_search(
    query: Annotated[str, typer.Argument(help="Search query (file name)")],
    count: Annotated[int, typer.Option("--count", "-n", help="Number of results")] = 20,
) -> None:
    """Search for files in Google Drive."""
    from google_cl.services.drive import DriveService

    try:
        auth = get_credentials("drive")
        drive = DriveService(auth.credentials)

        files = drive.search_files(name=query, max_results=count)

        if not files:
            rprint(f"[yellow]No files found matching '{query}'[/yellow]")
            return

        table = Table(title=f"🔍 Search Results for '{query}'")
        table.add_column("Name", style="cyan", max_width=40)
        table.add_column("Type", style="dim")
        table.add_column("Size", justify="right")
        table.add_column("ID", style="dim", max_width=25)

        for f in files:
            icon = "📁" if f.is_folder else "📄"
            table.add_row(f"{icon} {f.name}"[:40], f.type_name, f.size_formatted, f.id[:25])

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@drive_app.command("upload")
def drive_upload(
    file_path: Annotated[Path, typer.Argument(help="Local file path to upload")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="Name in Drive")] = None,
    folder: Annotated[str | None, typer.Option("--folder", "-f", help="Folder ID")] = None,
) -> None:
    """Upload a file to Google Drive."""
    from google_cl.services.drive import DriveService

    try:
        auth = get_credentials("drive")
        drive = DriveService(auth.credentials)

        result = drive.upload_file(file_path=file_path, name=name, folder_id=folder)
        rprint("[green]✓ File uploaded successfully![/green]")
        rprint(f"  Name: {result.name}")
        rprint(f"  ID: {result.id}")
        if result.web_view_link:
            rprint(f"  Link: {result.web_view_link}")

    except FileNotFoundError:
        rprint(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@drive_app.command("download")
def drive_download(
    file_id: Annotated[str, typer.Argument(help="File ID to download")],
    destination: Annotated[
        Path, typer.Option("--output", "-o", help="Output path")
    ] = Path("."),
) -> None:
    """Download a file from Google Drive."""
    from google_cl.services.drive import DriveService

    try:
        auth = get_credentials("drive")
        drive = DriveService(auth.credentials)

        # If destination is a directory, use file name
        if destination.is_dir():
            file_info = drive.get_file(file_id)
            destination = destination / file_info.name

        result = drive.download_file(file_id=file_id, destination=destination)
        rprint(f"[green]✓ File downloaded to: {result}[/green]")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@drive_app.command("mkdir")
def drive_mkdir(
    name: Annotated[str, typer.Argument(help="Folder name")],
    parent: Annotated[str | None, typer.Option("--parent", "-p", help="Parent folder ID")] = None,
) -> None:
    """Create a folder in Google Drive."""
    from google_cl.services.drive import DriveService

    try:
        auth = get_credentials("drive")
        drive = DriveService(auth.credentials)

        result = drive.create_folder(name=name, parent_id=parent)
        rprint("[green]✓ Folder created![/green]")
        rprint(f"  Name: {result.name}")
        rprint(f"  ID: {result.id}")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@drive_app.command("delete")
def drive_delete(
    file_id: Annotated[str, typer.Argument(help="File ID to delete")],
    permanent: Annotated[bool, typer.Option("--permanent", help="Permanently delete")] = False,
) -> None:
    """Delete a file from Google Drive."""
    from google_cl.services.drive import DriveService

    try:
        auth = get_credentials("drive")
        drive = DriveService(auth.credentials)

        drive.delete_file(file_id=file_id, permanent=permanent)
        if permanent:
            rprint("[green]✓ File permanently deleted[/green]")
        else:
            rprint("[green]✓ File moved to trash[/green]")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@drive_app.command("quota")
def drive_quota() -> None:
    """Show Google Drive storage quota."""
    from google_cl.services.drive import DriveService

    try:
        auth = get_credentials("drive")
        drive = DriveService(auth.credentials)

        quota = drive.get_storage_quota()

        def format_size(size: int) -> str:
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} PB"

        used = int(quota.get("usage", 0))
        limit = int(quota.get("limit", 0))
        percent = (used / limit * 100) if limit > 0 else 0

        rprint(Panel(
            f"[cyan]Used:[/cyan] {format_size(used)}\n"
            f"[cyan]Total:[/cyan] {format_size(limit)}\n"
            f"[cyan]Usage:[/cyan] {percent:.1f}%",
            title="💾 Storage Quota",
        ))

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


# ============================================================================
# Calendar Commands
# ============================================================================


@calendar_app.command("today")
def calendar_today() -> None:
    """Show today's events."""
    from google_cl.services.calendar import CalendarService

    try:
        auth = get_credentials("calendar")
        calendar = CalendarService(auth.credentials)

        events = calendar.get_today_events()

        if not events:
            rprint("[yellow]No events scheduled for today.[/yellow]")
            return

        table = Table(title="📅 Today's Events")
        table.add_column("Time", style="cyan")
        table.add_column("Event", style="white", max_width=40)
        table.add_column("Location", style="dim", max_width=30)

        for event in events:
            if event.all_day:
                time_str = "All day"
            else:
                # Parse and format time
                start_str = str(event.start)
                time_str = start_str.split("T")[1][:5] if "T" in start_str else start_str

            table.add_row(time_str, event.summary[:40], event.location[:30])

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@calendar_app.command("upcoming")
def calendar_upcoming(
    days: Annotated[int, typer.Option("--days", "-d", help="Days to look ahead")] = 7,
    count: Annotated[int, typer.Option("--count", "-n", help="Max events to show")] = 20,
) -> None:
    """Show upcoming events."""
    from google_cl.services.calendar import CalendarService

    try:
        auth = get_credentials("calendar")
        calendar = CalendarService(auth.credentials)

        events = calendar.get_upcoming_events(days=days, max_results=count)

        if not events:
            rprint(f"[yellow]No events in the next {days} days.[/yellow]")
            return

        table = Table(title=f"📅 Upcoming Events (Next {days} days)")
        table.add_column("Date", style="cyan")
        table.add_column("Time", style="cyan")
        table.add_column("Event", style="white", max_width=35)
        table.add_column("Location", style="dim", max_width=25)

        for event in events:
            start_str = str(event.start)
            if event.all_day:
                date_str = start_str[:10]
                time_str = "All day"
            elif "T" in start_str:
                parts = start_str.split("T")
                date_str = parts[0]
                time_str = parts[1][:5]
            else:
                date_str = start_str[:10]
                time_str = "-"

            table.add_row(date_str, time_str, event.summary[:35], event.location[:25])

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@calendar_app.command("add")
def calendar_add(
    title: Annotated[str, typer.Argument(help="Event title")],
    start: Annotated[str, typer.Option("--start", "-s", help="Start time (YYYY-MM-DD HH:MM)")],
    end: Annotated[str | None, typer.Option("--end", "-e", help="End time")] = None,
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    location: Annotated[str, typer.Option("--location", "-l", help="Location")] = "",
    all_day: Annotated[bool, typer.Option("--all-day", help="All-day event")] = False,
) -> None:
    """Create a new calendar event."""
    from google_cl.services.calendar import CalendarService

    try:
        auth = get_credentials("calendar")
        calendar = CalendarService(auth.credentials)

        # Parse start time
        try:
            start_dt = datetime.fromisoformat(start.replace(" ", "T"))
        except ValueError:
            rprint("[red]Invalid start time format. Use: YYYY-MM-DD HH:MM[/red]")
            raise typer.Exit(1) from None

        # Parse end time if provided
        end_dt = None
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace(" ", "T"))
            except ValueError:
                rprint("[red]Invalid end time format. Use: YYYY-MM-DD HH:MM[/red]")
                raise typer.Exit(1) from None

        event = calendar.create_event(
            summary=title,
            start=start_dt,
            end=end_dt,
            description=description,
            location=location,
            all_day=all_day,
        )

        rprint("[green]✓ Event created![/green]")
        rprint(f"  Title: {event.summary}")
        rprint(f"  ID: {event.id}")
        if event.html_link:
            rprint(f"  Link: {event.html_link}")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@calendar_app.command("quick")
def calendar_quick(
    text: Annotated[str, typer.Argument(help="Natural language event description")],
) -> None:
    """Create event from natural language (e.g., 'Meeting tomorrow at 3pm')."""
    from google_cl.services.calendar import CalendarService

    try:
        auth = get_credentials("calendar")
        calendar = CalendarService(auth.credentials)

        event = calendar.quick_add(text)

        rprint("[green]✓ Event created![/green]")
        rprint(f"  Title: {event.summary}")
        rprint(f"  Start: {event.start}")
        if event.html_link:
            rprint(f"  Link: {event.html_link}")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@calendar_app.command("delete")
def calendar_delete(
    event_id: Annotated[str, typer.Argument(help="Event ID to delete")],
) -> None:
    """Delete a calendar event."""
    from google_cl.services.calendar import CalendarService

    try:
        auth = get_credentials("calendar")
        calendar = CalendarService(auth.credentials)

        calendar.delete_event(event_id)
        rprint("[green]✓ Event deleted[/green]")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@calendar_app.command("calendars")
def calendar_list() -> None:
    """List all calendars."""
    from google_cl.services.calendar import CalendarService

    try:
        auth = get_credentials("calendar")
        calendar = CalendarService(auth.credentials)

        calendars = calendar.list_calendars()

        table = Table(title="📅 Your Calendars")
        table.add_column("Name", style="cyan")
        table.add_column("Primary", style="green")
        table.add_column("Timezone", style="dim")
        table.add_column("ID", style="dim", max_width=30)

        for cal in calendars:
            primary = "✓" if cal.is_primary else ""
            table.add_row(cal.summary, primary, cal.time_zone, cal.id[:30])

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


# ============================================================================
# Main App Commands
# ============================================================================


@app.command()
def version() -> None:
    """Show version information."""
    from google_cl import __version__
    rprint(f"[cyan]googlecl[/cyan] version [green]{__version__}[/green]")


@app.command()
def status() -> None:
    """Show status of all services."""
    from google_cl.services.calendar import CalendarService
    from google_cl.services.drive import DriveService
    from google_cl.services.gmail import GmailService

    auth = GoogleAuth()

    table = Table(title="🔍 GoogleCL Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")

    # Check authentication
    if auth.is_authenticated():
        table.add_row("Authentication", "[green]✓ Connected[/green]", str(DEFAULT_TOKEN_FILE))

        # Test each service
        try:
            gmail = GmailService(auth.credentials)
            profile = gmail.get_profile()
            table.add_row("Gmail", "[green]✓ Working[/green]", profile.get("emailAddress", ""))
        except Exception as e:
            table.add_row("Gmail", "[red]✗ Error[/red]", str(e)[:40])

        try:
            drive = DriveService(auth.credentials)
            if drive.test_connection():
                table.add_row("Drive", "[green]✓ Working[/green]", "")
            else:
                table.add_row("Drive", "[red]✗ Error[/red]", "Connection failed")
        except Exception as e:
            table.add_row("Drive", "[red]✗ Error[/red]", str(e)[:40])

        try:
            calendar = CalendarService(auth.credentials)
            if calendar.test_connection():
                table.add_row("Calendar", "[green]✓ Working[/green]", "")
            else:
                table.add_row("Calendar", "[red]✗ Error[/red]", "Connection failed")
        except Exception as e:
            table.add_row("Calendar", "[red]✗ Error[/red]", str(e)[:40])
    else:
        table.add_row("Authentication", "[yellow]✗ Not connected[/yellow]", "Run: googlecl auth login")
        table.add_row("Gmail", "[dim]- Unknown[/dim]", "")
        table.add_row("Drive", "[dim]- Unknown[/dim]", "")
        table.add_row("Calendar", "[dim]- Unknown[/dim]", "")

    console.print(table)


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
