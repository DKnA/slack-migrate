import os
import json
import time
from pathlib import Path
from slack_bolt import App
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

from slack_sdk import WebClient
admin_client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))

# Cache directory
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def get_cached_data(cache_name):
    """Get data from cache if it exists and is valid.

    Args:
        cache_name (str): Name of the cache file (without extension)

    Returns:
        dict: Cached data or None if no valid cache exists
    """
    cache_file = CACHE_DIR / f"{cache_name}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
            return cache_data["data"]
    except Exception as e:
        raise Exception(f"Error reading cache file {cache_file}: {e}")


def cache_data(cache_name, data):
    """Save data to cache with timestamp.

    Args:
        cache_name (str): Name of the cache file (without extension)
        data: Data to cache
    """
    cache_file = CACHE_DIR / f"{cache_name}.json"

    try:
        cache_content = {
            "timestamp": time.time(),
            "data": data
        }

        with open(cache_file, "w") as f:
            json.dump(cache_content, f)
    except Exception as e:
        raise Exception(f"Error writing to cache file {cache_file}: {e}")


def fetch_emoji(refresh=False):
    """Fetch all custom emoji from the workspace.

    Args:
        refresh (bool): Force refresh of cached data

    Returns:
        dict: Dictionary of emoji names and their URLs
    """
    cache_name = "emoji"

    if not refresh:
        cached_emoji = get_cached_data(cache_name)
        if cached_emoji is not None:
            return cached_emoji

    try:
        result = app.client.emoji_list()

        emoji_dict = result.get("emoji", {})

        cache_data(cache_name, emoji_dict)

        return emoji_dict
    except Exception as e:
        raise Exception(f"Error retrieving emoji: {e}")


def fetch_users(refresh=False):
    """Fetch all users from the workspace.

    Args:
        refresh (bool): Force refresh of cached data

    Returns:
        list: List of all user objects
    """
    cache_name = "users"

    if not refresh:
        cached_users = get_cached_data(cache_name)
        if cached_users is not None:
            return cached_users

    users = []
    cursor = None

    try:
        while True:
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor

            result = app.client.users_list(**params)

            users_batch = result["members"]
            users.extend(users_batch)

            cursor = result.get("response_metadata", {}).get("next_cursor")

            if not cursor:
                break

        cache_data(cache_name, users)
        return users

    except Exception as e:
        raise Exception(f"Error retrieving all users: {e}")


def fetch_user_info(user_id, refresh=False):
    """Fetch information about a specific user.

    Args:
        user_id (str): The Slack user ID to look up
        refresh (bool): Force refresh of all users data

    Returns:
        dict: User information or empty dict if not found/error
    """
    all_users = fetch_users(refresh=refresh)

    for user in all_users:
        if user["id"] == user_id:
            return user

    return {}


def enrich_channels_with_creator_info(channels):
    """Enrich channel objects with creator user details.

    Args:
        channels (list): List of channel objects

    Returns:
        list: Channels with enriched creator information
    """
    # Get all users
    users = fetch_users()

    # Create a mapping of user IDs to user objects for efficient lookup
    user_map = {user['id']: user for user in users}

    # Enrich each channel with creator details
    for channel in channels:
        creator_id = channel.get('creator')
        if creator_id and creator_id in user_map:
            user = user_map[creator_id]
            profile = user.get('profile', {})

            # Replace creator ID with structured object
            channel['creator'] = {
                'id': creator_id,
                'real_name': user.get('real_name', ''),
                'email': profile.get('email', ''),
                'display_name': profile.get('display_name', '')
            }
        else:
            channel['creator'] = {
                'id': creator_id,
                'real_name': None,
                'email': None,
                'display_name': None
            }

    return channels


def fetch_channels(refresh=False):
    """Core function to fetch all public channels with pagination.

    Args:
        refresh (bool): Force refresh of cached data

    Returns:
        list: List of all channel objects with enriched creator info
    """
    cache_name = "channels"

    # Check cache first if not forcing refresh
    if not refresh:
        cached_channels = get_cached_data(cache_name)
        if cached_channels is not None:
            return cached_channels

    channels = []
    cursor = None

    while True:
        try:
            params = {
                "types": "public_channel",
                "limit": 100
            }

            if cursor:
                params["cursor"] = cursor

            result = app.client.conversations_list(**params)

            channels_batch = result["channels"]
            channels.extend(channels_batch)

            cursor = result.get("response_metadata", {}).get("next_cursor")

            if not cursor:
                break

        except Exception as e:
            raise Exception(f"Error retrieving channels: {e}")

    enriched_channels = enrich_channels_with_creator_info(channels)

    cache_data(cache_name, enriched_channels)

    return enriched_channels


def get_channel_info(channel_id):
    """Get information about a Slack channel.

    Args:
        channel_id (str): ID of the channel

    Returns:
        dict: Channel information

    Raises:
        Exception: If API call fails with an error
    """
    try:
        response = app.client.conversations_info(channel=channel_id)
        if response.get('ok', False):
            return response.get('channel', {})
        else:
            raise Exception(response.get('error', 'Unknown error'))
    except Exception as e:
        raise Exception(f"Error getting channel info: {str(e)}")


def rename_channel(channel_id, new_name):
    """Rename a Slack channel using Bolt.

    Args:
        channel_id (str): ID of the channel to rename
        new_name (str): New name for the channel (without the # prefix)

    Returns:
        bool: True if successful, False otherwise

    Raises:
        Exception: If API call fails with an error
    """
    try:
        channel_info = get_channel_info(channel_id)
        is_member = channel_info.get('is_member', False)

        if not is_member:
            try:
                if not channel_info.get('is_private', True):
                    admin_client.conversations_join(channel=channel_id)
                else:
                    raise Exception(
                        f"Bot is not a member of private channel {channel_id}. Please invite the bot first.")
            except Exception as e:
                raise Exception(
                    f"Failed to join channel {channel_id}: {str(e)}")

        if new_name.startswith('#'):
            new_name = new_name[1:]

        response = admin_client.conversations_rename(
            channel=channel_id,
            name=new_name
        )
        return response.get('ok', False)

    except Exception as e:
        raise Exception(f"Error renaming channel {channel_id}: {str(e)}")


def archive_channel(channel_id):
    """Archive a Slack channel using Bolt.

    Args:
        channel_id (str): ID of the channel to archive

    Returns:
        bool: True if successful, False otherwise

    Raises:
        Exception: If API call fails with an error
    """
    try:
        channel_info = get_channel_info(channel_id)
        is_member = channel_info.get('is_member', False)

        if not is_member:
            try:
                if not channel_info.get('is_private', True):
                    app.client.conversations_join(channel=channel_id)
                else:
                    raise Exception(
                        f"Bot is not a member of private channel {channel_id}. Please invite the bot first.")
            except Exception as e:
                raise Exception(
                    f"Failed to join channel {channel_id}: {str(e)}")

        response = app.client.conversations_archive(channel=channel_id)
        return response.get('ok', False)

    except Exception as e:
        raise Exception(f"Error archiving channel {channel_id}: {str(e)}")
