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
├── methods/         # Command implementations
    ├── channels.py
    ├── emoji.py
    └── users.py

```

## CLI Usage

The tool provides several command groups for different Slack data types:

### Channels Commands

```bash
slack-migrate channels list [--refresh] [--format FORMAT]
slack-migrate channels info CHANNEL_ID
slack-migrate channels rename CHANNEL_ID NEW_NAME
slack-migrate channels archive CHANNEL_ID
```

### Emoji Commands

```bash
slack-migrate emoji list [--refresh] [--format FORMAT]
slack-migrate emoji export [--refresh] [--output-dir DIR]
```

### Users Commands

```bash
slack-migrate users list [--refresh] [--format FORMAT]
slack-migrate users info USER_ID [--refresh]
```

### Common Options

- `--refresh`: Force refresh the cache and fetch new data from Slack
- `--format`: Output format (default: table, options: table, json, csv)
- `--output-dir`: Directory for exported files (for emoji export)

## Caching

The tool implements a caching system to reduce API calls:
- Cache files are stored in the `cache` directory
- Use `--refresh` flag to force a fresh data fetch
- Cache is automatically invalidated after 24 hours

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 