import click
from ..api import fetch_users
from tabulate import tabulate


@click.group('users')
def users_group():
    """Commands related to Slack emoji."""
    pass


@users_group.command('fetch')
@click.option('--refresh', is_flag=True, help='Force refresh of cached users data')
def fetch_users_cmd(refresh):
    """Fetch all users from Slack workspace."""
    
    users_dict = fetch_users(refresh=refresh)
    
    click.echo(f"total {len(users_dict)}")
    
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
