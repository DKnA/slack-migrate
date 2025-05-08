# Slack Migration Tools

A Python-based CLI tool for extracting and managing Slack workspace data, including channels, users, and emoji.

## Features

- Extract and manage Slack channels
- Export and manage emoji
- User information retrieval
- Caching system for API responses
- Command-line interface for easy interaction

## Prerequisites

- Python 3.8 or higher
- Slack workspace with appropriate permissions
- Slack API tokens (Bot Token and User Token)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/slack-migration.git
cd slack-migration
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
SLACK_BOT_TOKEN=your_bot_token
SLACK_USER_TOKEN=your_user_token
SLACK_SIGNING_SECRET=your_signing_secret
```

## Development Setup

1. Install the package in development mode:
```bash
pip install -e .
```

2. The project structure:
```
slack_migrate/
├── api.py           # Core API functionality
├── cli.py           # CLI interface
└── methods/         # Command implementations
    ├── channels.py
    ├── emoji.py
    └── users.py

```

## CLI Usage

The tool provides several command groups for different Slack data types:

### Channels Commands

```bash
slack-migrate channels fetch [--type TYPE] [--refresh] [--creator CREATOR] [--archived-days-ago DAYS] [--created-days-ago DAYS] [--zero-members] [--csv]
slack-migrate channels archive CHANNEL_ID [--dry-run]
slack-migrate channels prefix PREFIX [CHANNEL_ID] [--dry-run]
```

### Emoji Commands

```bash
slack-migrate emoji fetch [--refresh] [--csv]
slack-migrate emoji download [--refresh]
```

### Users Commands

```bash
slack-migrate users fetch [--refresh] [--csv]
```

### Common Options

- `--refresh`: Force refresh the cache and fetch new data from Slack
- `--dry-run`: Preview actions without executing them (for archive and prefix commands)
- `--csv`: Export data to CSV file (for fetch commands)

### Channel Type Options
- `--type`: Filter channels by type (choices: all, active, archived; default: all)
- `--creator`: Filter channels by creator ID or email
- `--archived-days-ago`: Filter channels archived within specified number of days
- `--created-days-ago`: Filter channels created within specified number of days
- `--zero-members`: Only show channels with zero members

## Caching

The tool implements a caching system to reduce API calls:
- Cache files are stored in the `cache` directory
- Use `--refresh` flag to force a fresh data fetch
- Cache is automatically invalidated after 24 hours

## Examples

Here are some common usage examples of the CLI tool:

### Archive Empty Channels
To find and archive all channels that have zero members:

```bash
# First, list all empty channels
slack-migrate channels fetch --zero-members

# Review the output and if you want to proceed, pipe the channel IDs to archive
slack-migrate channels fetch --zero-members | tail -n +2 | awk '{print $1}' | slack-migrate channels archive

# Or use --dry-run first to preview what would be archived
slack-migrate channels fetch --zero-members | tail -n +2 | awk '{print $1}' | slack-migrate channels archive --dry-run
```