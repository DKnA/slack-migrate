import click
import csv as csv_lib
from ..api import fetch_users
from tabulate import tabulate


@click.group('users')
def users_group():
    """Commands related to Slack emoji."""
    pass


@users_group.command('fetch')
@click.option('--refresh', is_flag=True, help='Force refresh of cached users data')
@click.option('--csv', is_flag=True, help='Export users to CSV file')
def fetch_users_cmd(refresh, csv):
    """Fetch all users from Slack workspace."""
    
    users_dict = fetch_users(refresh=refresh)
    
    click.echo(f"total {len(users_dict)}")
    
    if csv:
        # Define CSV fields based on the sample data
        fields = [
            'id', 'team_id', 'name', 'deleted', 'color', 'real_name',
            'tz', 'tz_label', 'tz_offset', 'is_admin', 'is_owner',
            'is_primary_owner', 'is_restricted', 'is_ultra_restricted',
            'is_bot', 'is_app_user', 'updated', 'is_email_confirmed',
            'who_can_share_contact_card'
        ]
        
        # Profile fields to include
        profile_fields = [
            'title', 'phone', 'skype', 'real_name', 'real_name_normalized',
            'display_name', 'display_name_normalized', 'status_text',
            'status_emoji', 'status_expiration', 'avatar_hash',
            'always_active', 'first_name', 'last_name', 'email'
        ]
        
        # Create CSV file
        with open('data/users.csv', 'w', newline='') as csvfile:
            writer = csv_lib.DictWriter(csvfile, fieldnames=fields + [f'profile_{f}' for f in profile_fields])
            writer.writeheader()
            
            for user in users_dict:
                row = {field: user.get(field, '') for field in fields}
                
                # Add profile fields with prefix
                profile = user.get('profile', {})
                for field in profile_fields:
                    row[f'profile_{field}'] = profile.get(field, '')
                
                writer.writerow(row)
        
        click.echo("Users exported to users.csv")
    else:
        # Original table output
        rows = []
        for u in users_dict:
            p = u.get('profile', {})
            rows.append([
                u['id'],
                f"@{u['name']}",
                p.get('real_name', ''),
                p.get('email', '<no email>')
            ])
        
        click.echo(tabulate(rows, tablefmt="plain"))
