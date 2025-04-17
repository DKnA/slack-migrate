import click
import os
import urllib.request
import urllib.error
from collections import defaultdict
from urllib.parse import urlparse
from ..api import fetch_emoji


def download_emoji_files(emoji_dict):
    """Download emoji files to local folder.

    Args:
        emoji_dict (dict): Dictionary of emoji names and URLs
    """
    # Create emoji files directory
    emoji_dir = os.path.join("data", "custom-emojis-files")
    os.makedirs(emoji_dir, exist_ok=True)

    click.echo(f"Downloading emoji files to {emoji_dir}...")

    # Track statistics
    total = len(emoji_dict)
    downloaded = 0
    aliases = 0
    failed = 0

    with click.progressbar(emoji_dict.items(), label='Downloading', length=total) as items:
        for emoji_name, emoji_url in items:
            # Skip aliases
            if emoji_url.startswith('alias:'):
                aliases += 1
                continue

            try:
                # Get file extension from URL
                parsed_url = urlparse(emoji_url)
                path = parsed_url.path
                _, ext = os.path.splitext(path)

                # If no extension found, default to .png
                if not ext:
                    ext = '.png'

                # Create safe filename
                safe_name = emoji_name.replace(':', '').replace('/', '_')
                file_path = os.path.join(emoji_dir, f"{safe_name}{ext}")

                # Download file using urllib instead of requests
                try:
                    urllib.request.urlretrieve(emoji_url, file_path)
                    downloaded += 1
                except (urllib.error.URLError, urllib.error.HTTPError) as e:
                    failed += 1
            except Exception as e:
                failed += 1

    # Display summary
    click.echo(f"\nEmoji download complete:")
    click.echo(f"  - Total: {total}")
    click.echo(f"  - Downloaded: {downloaded}")
    click.echo(f"  - Aliases (skipped): {aliases}")
    click.echo(f"  - Failed: {failed}")


@click.group('emoji')
def emoji_group():
    """Commands related to Slack emoji."""
    pass


@emoji_group.command('fetch')
@click.option('--refresh', is_flag=True, help='Force refresh of cached emoji data')
def fetch_emoji_cmd(refresh):
    """Fetch custom emoji from Slack workspace."""

    emoji_dict = fetch_emoji(refresh=refresh)
    for emoji_name, emoji_url in emoji_dict.items():
        click.echo(f":{emoji_name}:")


@emoji_group.command('download')
@click.option('--refresh', is_flag=True, help='Force refresh of cached emoji data')
def download_emoji_cmd(refresh):
    """Download emoji image files."""

    emoji_dict = fetch_emoji(refresh=refresh)
    click.echo(f"Found {len(emoji_dict)} custom emoji.")
    download_emoji_files(emoji_dict)
