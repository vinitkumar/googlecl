=========
GoogleCL
=========

.. image:: https://img.shields.io/pypi/v/google_cl.svg
        :target: https://pypi.python.org/pypi/google_cl

.. image:: https://img.shields.io/pypi/pyversions/google_cl.svg
        :target: https://pypi.python.org/pypi/google_cl

.. image:: https://readthedocs.org/projects/google-cl/badge/?version=latest
        :target: https://google-cl.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

**Command-line interface for Google services - Gmail, Drive, and Calendar**

GoogleCL provides a modern, intuitive command-line interface to interact with Google services. Manage your emails, files, and calendar events directly from your terminal.

* Free software: Apache Software License 2.0
* Documentation: https://google-cl.readthedocs.io

Features
--------

📧 **Gmail**
  - List and read emails from your inbox
  - Send emails with plain text or HTML
  - Search emails using Gmail query syntax
  - Manage labels

📁 **Google Drive**
  - List and search files
  - Upload and download files
  - Create folders
  - Check storage quota
  - Delete files (trash or permanent)

📅 **Google Calendar**
  - View today's events
  - List upcoming events
  - Create new events
  - Quick add events using natural language
  - Manage multiple calendars

Installation
------------

Using `uv` (recommended)::

    uv pip install googlecl

Using pip::

    pip install googlecl

From source::

    git clone https://github.com/vinitkumar/googlecl.git
    cd googlecl
    uv pip install -e .

Quick Start
-----------

1. **Set up Google Cloud credentials**:

   - Go to https://console.cloud.google.com/
   - Create a new project or select an existing one
   - Enable the Gmail, Drive, and Calendar APIs
   - Go to APIs & Services > Credentials
   - Create an OAuth 2.0 Client ID (Desktop application)
   - Download the JSON file

2. **Configure GoogleCL**::

    # Show configuration paths
    googlecl auth info
    
    # Copy your credentials.json to the config directory
    mkdir -p ~/.config/googlecl
    cp ~/Downloads/credentials.json ~/.config/googlecl/

3. **Authenticate**::

    googlecl auth login

4. **Start using GoogleCL**::

    # Check your inbox
    googlecl gmail inbox
    
    # List Drive files
    googlecl drive list
    
    # Show today's calendar events
    googlecl calendar today

Usage Examples
--------------

**Gmail**::

    # List 10 emails from inbox
    googlecl gmail inbox -n 10
    
    # Show only unread emails
    googlecl gmail inbox --unread
    
    # Read a specific email
    googlecl gmail read MESSAGE_ID
    
    # Send an email
    googlecl gmail send --to user@example.com --subject "Hello" --body "Hi there!"
    
    # Search emails
    googlecl gmail search "from:boss@company.com is:unread"
    
    # List all labels
    googlecl gmail labels

**Google Drive**::

    # List files
    googlecl drive list
    
    # Search for files
    googlecl drive search "report"
    
    # Upload a file
    googlecl drive upload myfile.pdf
    
    # Download a file
    googlecl drive download FILE_ID -o ~/Downloads/
    
    # Create a folder
    googlecl drive mkdir "New Folder"
    
    # Check storage quota
    googlecl drive quota

**Google Calendar**::

    # Show today's events
    googlecl calendar today
    
    # Show upcoming events (next 7 days)
    googlecl calendar upcoming
    
    # Show next 30 days
    googlecl calendar upcoming --days 30
    
    # Create an event
    googlecl calendar add "Team Meeting" --start "2024-01-15 10:00" --end "2024-01-15 11:00"
    
    # Quick add (natural language)
    googlecl calendar quick "Lunch with John tomorrow at noon"
    
    # List all calendars
    googlecl calendar calendars

Authentication
--------------

GoogleCL uses OAuth 2.0 for authentication. Your credentials are stored locally at:

- **Credentials file**: ``~/.config/googlecl/credentials.json``
- **Token file**: ``~/.config/googlecl/token.json``

Commands::

    # Check authentication status
    googlecl auth status
    
    # Login (authenticate)
    googlecl auth login
    
    # Force re-authentication
    googlecl auth login --force
    
    # Logout (remove tokens)
    googlecl auth logout
    
    # Show configuration info
    googlecl auth info

Development
-----------

Clone the repository::

    git clone https://github.com/vinitkumar/googlecl.git
    cd googlecl

Set up development environment::

    uv venv
    source .venv/bin/activate
    uv pip install -e ".[dev]"

Run tests::

    pytest

Run linting::

    ruff check src tests
    mypy src

Contributing
------------

Contributions are welcome! Please read `CONTRIBUTING.rst` for guidelines.

License
-------

This project is licensed under the Apache License 2.0 - see the `LICENSE` file for details.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
