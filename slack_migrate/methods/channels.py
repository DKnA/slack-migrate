import click
from ..api import fetch_channels, archive_channel, rename_channel, get_channel_info
import time
from datetime import datetime, timedelta
from tabulate import tabulate
import sys
from slack_bolt import App
import csv as csv_lib


def filter_channels_by_type(channels, filter_type):
    """Filter channels based on the requested type.

    Args:
        channels (list): List of channel data dictionaries
        filter_type (str): Type of channels to filter by
    """
    if filter_type == "active":
        return [c for c in channels if not c.get('is_archived', False)]
    elif filter_type == "archived":
        return [c for c in channels if c.get('is_archived', False)]
    else:
        return channels


def filter_channels_by_creator(channels, creator):
    """Filter channels based on the requested creator.

    Args:
        channels (list): List of channel data dictionaries
        creator (str): Creator ID or email

    Returns:
        list: Channels created by the specified creator
    """
    is_email = '@' in creator

    filtered_channels = []
    for channel in channels:
        creator_info = channel.get('creator', {})

        if is_email and creator_info.get('email') == creator:
            filtered_channels.append(channel)
        elif not is_email and creator_info.get('id') == creator:
            filtered_channels.append(channel)

    return filtered_channels


def filter_channels_by_archived_days_ago(channels, archived_days_ago):
    """Filter channels based on the requested archived days ago.

    Args:
        channels (list): List of channel data dictionaries
        archived_days_ago (int): Number of days to look back for when channel was archived
    """
    cutoff_date = datetime.now() - timedelta(days=archived_days_ago)
    cutoff_timestamp = cutoff_date.timestamp()

    return [
        channel for channel in channels
        if channel.get('is_archived', False) and
        # Convert updated from milliseconds to seconds for comparison
        float(channel.get('updated', 0)) / 1000 >= cutoff_timestamp
    ]


def filter_channels_by_created_days_ago(channels, created_days_ago):
    """Filter channels based on the requested created days ago.

    Args:
        channels (list): List of channel data dictionaries  
        created_days_ago (int): Number of days to look back for when channel was created

    Returns:
        list: Channels created within the specified timeframe
    """
    cutoff_date = datetime.now() - timedelta(days=created_days_ago)
    cutoff_timestamp = cutoff_date.timestamp()

    return [
        channel for channel in channels
        # created is already in seconds
        if float(channel.get('created', 0)) >= cutoff_timestamp
    ]


def find_zero_member_channels(channels):
    """Find channels with zero members.

    Args:
        channels (list): List of channel data dictionaries

    Returns:
        list: Channels with zero members
    """
    return [c for c in channels if c.get('num_members', 0) == 0]


# Command group definition


@click.group('channels')
def channels_group():
    """Commands related to Slack channels."""
    pass


@channels_group.command('fetch')
@click.option('--type', type=click.Choice(['all', 'active', 'archived']), default='all',
              help='Which channels to return')
@click.option('--refresh', is_flag=True, help='Force refresh of cached channel data')
@click.option('--creator', type=click.STRING, help='Channel creator ID or email')
@click.option('--archived-days-ago', type=click.INT, help='Maximum number of days to look back for when channel was archived')
@click.option('--created-days-ago', type=click.INT, help='Maximum number of days to look back for when channel was created')
@click.option('--zero-members', is_flag=True, help='Only return channels with zero members')
@click.option('--csv', is_flag=True, help='Export channels to CSV file')
def fetch_channels_cmd(type, refresh, creator, archived_days_ago, created_days_ago, zero_members, csv):
    """Fetch channels from Slack workspace."""
    channels_dict = fetch_channels(refresh=refresh)
    filtered_channels_dict = filter_channels_by_type(channels_dict, type)

    if creator:
        filtered_channels_dict = filter_channels_by_creator(
            filtered_channels_dict, creator)

    if archived_days_ago:
        filtered_channels_dict = filter_channels_by_archived_days_ago(
            filtered_channels_dict, archived_days_ago)

    if created_days_ago:
        filtered_channels_dict = filter_channels_by_created_days_ago(
            filtered_channels_dict, created_days_ago)

    if zero_members:
        filtered_channels_dict = [
            c for c in filtered_channels_dict if c.get('num_members', 0) == 0]

    click.echo(f"total {len(filtered_channels_dict)}")

    if csv:
        # Define CSV fields based on the channel data
        fields = [
            'id', 'name', 'num_members', 'created', 'updated', 'is_archived',
            'creator_id', 'creator_email', 'topic', 'purpose'
        ]
        
        # Create CSV file
        with open('data/channels.csv', 'w', newline='') as csvfile:
            writer = csv_lib.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            
            for channel in filtered_channels_dict:
                created_ts = channel.get('created', 0)
                updated_ts = channel.get('updated', 0)
                
                # Format timestamps
                created_date = datetime.fromtimestamp(int(created_ts)).strftime('%Y-%m-%d %H:%M:%S') if created_ts else ''
                updated_date = datetime.fromtimestamp(int(updated_ts) / 1000).strftime('%Y-%m-%d %H:%M:%S') if updated_ts else ''
                
                creator_info = channel.get('creator', {})
                creator_email = creator_info.get('email', '') if isinstance(creator_info, dict) else ''
                creator_id = creator_info.get('id', '') if isinstance(creator_info, dict) else ''
                
                row = {
                    'id': channel.get('id', ''),
                    'name': channel.get('name', ''),
                    'num_members': channel.get('num_members', 0),
                    'created': created_date,
                    'updated': updated_date,
                    'is_archived': 'true' if channel.get('is_archived', False) else 'false',
                    'creator_id': creator_id,
                    'creator_email': creator_email,
                    'topic': channel.get('topic', {}).get('value', ''),
                    'purpose': channel.get('purpose', {}).get('value', '')
                }
                
                writer.writerow(row)
        
        click.echo("Channels exported to channels.csv")
    else:
        # Original table output
        rows = []
        for channel in filtered_channels_dict:
            created_ts = channel.get('created', 0)
            updated_ts = channel.get('updated', 0)

            # Format created (in seconds)
            if created_ts:
                created_date = datetime.fromtimestamp(
                    int(created_ts)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_date = '<created unknown>'

            # Format updated (in milliseconds)
            if updated_ts:
                # Convert milliseconds to seconds for datetime
                updated_date = datetime.fromtimestamp(
                    int(updated_ts) / 1000).strftime('%Y-%m-%d %H:%M:%S')
            else:
                updated_date = '<updated unknown>'

            creator_info = channel.get('creator', {})
            creator_email = creator_info.get(
                'email', '') if isinstance(creator_info, dict) else ''

            rows.append([
                channel.get('id', ''),
                f"#{channel.get('name', '')}",
                channel.get('num_members', 0),
                created_date,
                updated_date,
                creator_email,
                "archived" if channel.get('is_archived', False) else "active",
            ])

        click.echo(tabulate(rows, tablefmt="plain"))


@channels_group.command('archive')
@click.argument('channel_id', required=False)
@click.option('--dry-run', is_flag=True, help='Preview actions without executing them')
def archive_channels_cmd(channel_id, dry_run):
    """Archive Slack channels from a list of channel IDs.

    CHANNEL_ID is an optional single channel ID to archive.
    If not provided, channel IDs will be read from stdin.

    Example usage:
        slack_migrate channels archive C01234ABCDE
        cat channel_ids.txt | slack_migrate channels archive
        echo "C01234ABCDE" | slack_migrate channels archive
    """
    channel_ids = []

    if channel_id:
        channel_ids = [channel_id]
    else:
        for line in sys.stdin:
            line = line.strip()
            if line:
                channel_ids.append(line)

    if not channel_ids:
        click.echo(
            "No channel IDs provided. Either specify a channel ID or pipe a list of channel IDs to this command.")
        return

    if dry_run:
        click.echo("DRY RUN: The following channels would be archived:")
        for ch_id in channel_ids:
            click.echo(f"  - {ch_id}")
        return

    success_count = 0
    failed_channels = []

    with click.progressbar(channel_ids, label='Archiving channels') as bar:
        for ch_id in bar:
            try:
                success = archive_channel(ch_id)
                success = True
                if success:
                    success_count += 1
                else:
                    failed_channels.append((ch_id, "API call returned false"))
            except Exception as e:
                failed_channels.append((ch_id, str(e)))

    # Report results
    click.echo(f"Successfully archived {success_count} channel(s).")

    if failed_channels:
        click.echo(f"Failed to archive {len(failed_channels)} channel(s):")
        for ch_id, error in failed_channels:
            click.echo(f"  - {ch_id}: {error}")


@channels_group.command('prefix')
@click.argument('prefix', required=True)
@click.argument('channel_id', required=False)
@click.option('--dry-run', is_flag=True, help='Preview actions without executing them')
def prefix_channels_cmd(prefix, channel_id, dry_run):
    """Add a prefix to Slack channel names.

    PREFIX is the prefix to add to channel names (without the # symbol).
    CHANNEL_ID is an optional single channel ID to rename.
    If CHANNEL_ID is not provided, channel IDs will be read from stdin.

    The new channel name will follow the pattern: {prefix}-{old-channel-name}
    Channels that already start with the prefix will be skipped.

    Example usage:
        slack_migrate channels prefix archived C01234ABCDE
        cat channel_ids.txt | slack_migrate channels prefix team-x
        echo "C01234ABCDE" | slack_migrate channels prefix old
    """
    if prefix.startswith('#'):
        prefix = prefix[1:]
    if prefix.endswith('-'):
        prefix = prefix[:-1]

    channel_ids = []
    if channel_id:
        channel_ids = [channel_id]
    else:
        for line in sys.stdin:
            line = line.strip()
            if line:
                channel_ids.append(line)

    if not channel_ids:
        click.echo(
            "No channel IDs provided. Either specify a channel ID or pipe a list of channel IDs to this command.")
        return

    click.echo(f"Found {len(channel_ids)} channel(s) to process.")

    to_rename = []
    skipped = []

    for ch_id in channel_ids:
        try:
            channel_info = get_channel_info(ch_id)
            current_name = channel_info.get('name', '')

            if current_name.startswith(f"{prefix}-"):
                skipped.append((ch_id, current_name))
            else:
                new_name = f"{prefix}-{current_name}"
                to_rename.append((ch_id, current_name, new_name))
        except Exception as e:
            click.echo(f"Error getting info for channel {ch_id}: {str(e)}")

    if dry_run:
        click.echo("DRY RUN: The following channels would be renamed:")
        for ch_id, old_name, new_name in to_rename:
            click.echo(f"  - {ch_id} ({old_name}) → {new_name}")

        if skipped:
            click.echo(
                "\nThe following channels would be skipped (already have prefix):")
            for ch_id, name in skipped:
                click.echo(f"  - {ch_id} ({name})")
        return

    success_count = 0
    failed_channels = []

    with click.progressbar(to_rename, label='Renaming channels') as bar:
        for ch_id, old_name, new_name in bar:
            try:
                success = rename_channel(ch_id, new_name)
                if success:
                    success_count += 1
                else:
                    failed_channels.append(
                        (ch_id, old_name, new_name, "API call returned false"))
            except Exception as e:
                failed_channels.append((ch_id, old_name, new_name, str(e)))

    click.echo(f"Successfully renamed {success_count} channel(s).")

    if skipped:
        click.echo(f"Skipped {len(skipped)} channel(s) (already have prefix):")
        for ch_id, name in skipped:
            click.echo(f"  - {ch_id} ({name})")

    if failed_channels:
        click.echo(f"Failed to rename {len(failed_channels)} channel(s):")
        for ch_id, old_name, new_name, error in failed_channels:
            click.echo(f"  - {ch_id} ({old_name} → {new_name}): {error}")
