"""
snaps-source.py - Building snaps from source and promoting them to snapstore

"""

import click
import sh
import os
import glob
import re
import yaml
import operator
import sys
from urllib.parse import urlparse
from jinja2 import Template
from pathlib import Path
from sdk import lp


def _render(tmpl, context):
    """ Renders a jinja template with context
    """
    template = Template(tmpl)
    return template.render(context)


@click.group()
def cli():
    pass

@cli.command()
@click.option('--repo', help='Git repository to create a new branch on', required=True)
@click.option('--from-branch', help='Current git branch to checkout', required=True, default='master')
@click.option('--to-branch', help='Git branch to create, this is typically upstream k8s version', required=True)
@click.option('--dry-run', is_flag=True)
def branch(repo, from_branch, to_branch, dry_run):
    """ Creates a git branch based on the upstream snap repo and a version to branch as. This will also update
    the snapcraft.yaml with the correct version to build the snap from in that particular branch.

    Usage:

    snaps-source.py branch --repo git+ssh://$LPCREDS@git.launchpad.net/snap-kubectl --from-branch master --to-branch 1.13.2
    """
    try:
        sh.git('ls-remote', '--exit-code', '--heads', repo, to_branch)
        click.echo(f'{to_branch} already exists, exiting.')
        sys.exit(0)
    except sh.ErrorReturnCode as e:
        click.echo(f'{to_branch} does not exist, continuing...')

    snap_basename = urlparse(repo)
    snap_basename = Path(snap_basename.path).name
    if snap_basename.endswith('.git'):
        snap_basename = snap_basename.rstrip('.git')
    sh.rm('-rf', snap_basename)
    sh.git.clone(repo, branch=from_branch)
    sh.git.config('user.email', 'cdkbot@gmail.com', _cwd=snap_basename)
    sh.git.config('user.name', 'cdkbot', _cwd=snap_basename)
    sh.git.checkout('-b', to_branch, _cwd=snap_basename)

    snapcraft_fn = Path(snap_basename) / 'snapcraft.yaml.in'
    snapcraft_fn_tpl = Path(snap_basename) / 'snapcraft.yaml.in'
    if not snapcraft_fn_tpl.exists():
        click.echo(f'{snapcraft_fn_tpl} not found')
        sys.exit(1)
    snapcraft_yml = snapcraft_fn_tpl.read_text()
    snapcraft_yml = _render(snapcraft_yml, {'K8SVERSION': to_branch})
    snapcraft_fn.write_text(yaml.dump(snapcraft_yml,
                                      default_flow_style=False,
                                      indent=2))
    if not dry_run:
        sh.git.add('.', _cwd=snap_basename)
        sh.git.commit('-m', f'Creating branch {to_branch}', _cwd=snap_basename)
        sh.git.push(repo, to_branch, _cwd=snap_basename)


@cli.command()
@click.option('--snap', required=True, multiple=True, help='Snaps to build')
@click.option('--version', required=True, help='Version of k8s to build')
@click.option(
    '--track', required=True,
    help='Snap track to release to, format as: `[<track>/]<risk>[/<branch>]`')
@click.option('--owner', required=True, default='cdkbot',
              help='LP owner with access to managing the snap builds')
@click.option('--dry-run', is_flag=True)
def builder(snap, version, track, owner, dry_run):
    """ Creates an new LP builder for snaps

    Usage:

    snaps.py builder --snap kubectl --snap kube-proxy --version 1.13.2
    """
    _client = lp.Client(stage='production')
    _client.login()
    owner = _client.owner(owner)
    for _snap in snap:
        is_exists = _client.snaps.total_size > 0
        if not is_exists:
            continue
        params = (_snap, owner, version, track)
        if dry_run:
            click.echo("dry-run only:")
            click.echo(f"  > creating builder for {params}")
        else:
            _client.create_snap_builder(*params)


@cli.command()
@click.option('--result-dir', required=True, default='release/snap/build',
              help='Path of resulting snap builds')
@click.option('--dry-run', is_flag=True)
def push(result_dir, dry_run):
    """ Promote to a snapstore channel/track

    Usage:

       tox -e py36 -- python3 snaps.py push --result-dir ./release/snap/build
    """
    # TODO: Verify channel is a ver/chan string
    #   re: [\d+\.]+\/(?:edge|stable|candidate|beta)
    for fname in glob.glob(f'{result_dir}/*.snap'):
        try:
            click.echo(f'Running: snapcraft push {fname}')
            if dry_run:
                click.echo("dry-run only:")
                click.echo(f"  > snapcraft push {fname}")
            else:
                for line in sh.snapcraft.push(fname, _iter=True):
                    click.echo(line.strip())
        except sh.ErrorReturnCode_2 as e:
            click.echo('Failed to upload to snap store')
            click.echo(e.stdout)
            click.echo(e.stderr)
        except sh.ErrorReturnCode_1 as e:
            click.echo('Failed to upload to snap store')
            click.echo(e.stdout)
            click.echo(e.stderr)

@cli.command()
@click.option('--name', required=True, help='Snap name to release')
@click.option('--channel', required=True, help='Snapstore channel to release to')
@click.option('--version', required=True, help='Snap application version to release')
@click.option('--dry-run', is_flag=True)
def release(name, channel, version, dry_run):
    """ Release the most current revision snap to channel
    """
    re_comp = re.compile("[ \t+]{2,}")
    revision_list = sh.snapcraft.revisions(name)
    revision_list = revision_list.stdout.decode().splitlines()[1:]
    revision_parsed = {}
    for line in revision_list:
        rev, uploaded, arch, upstream_version, channels = re_comp.split(line)
        if upstream_version != version:
            continue
        revision_parsed[rev] = {
            'rev': rev,
            'uploaded': uploaded,
            'arch': arch,
            'version': upstream_version,
            'channels': channels
        }
    latest_release = max(revision_parsed.items(), key=operator.itemgetter(0))[1]
    click.echo(latest_release)
    if dry_run:
        click.echo("dry-run only:")
        click.echo(f"  > snapcraft release {name} {latest_release['rev']} {channel}")
    else:
        click.echo(sh.snapcraft.release(name, latest_release['rev'], channel))


if __name__ == "__main__":
    cli()
