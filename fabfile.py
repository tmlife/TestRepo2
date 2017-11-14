import os

from fabric.api import env, run
from fabric.decorators import task
from fabric.contrib.project import rsync_project
from fabric.contrib.files import upload_template, exists
#import pxssh

MINION_CONFIG = '/etc/salt/minion'
MINION_BIN = '/usr/bin/salt-minion'

env.hosts = ['10.157.141.51:2222']
#env.hosts = ['10.157.141.51']
env.user = 'dc_user'
env.passwords = {'dc_user@10.157.141.51:2222': '7dg5pwta'}
env.port = 2222
#env.root = '/home/dc_user/root'
#env.salt_roots = os.path.join(env.root, 'roots')


def bootstrap_salt():
    """
    Installs Salt minion if not already installed.
    """
    if not exists(MINION_BIN):
        run('wget -O - http://bootstrap.saltstack.org | sudo sh')


def sync_salt_roots():
    """
    Copies states and pillars using rsync to the remote server.
    """
    if not exists(env.salt_roots):
        run('mkdir {0}'.format(env.salt_roots))

    rsync_project(
        local_dir='roots',
        remote_dir=env.root,
        exclude='.git'
    )


def write_salt_minion_config():
    """
    Writes Salt minion config to the remote server.
    """
    context = {
        'salt_root': os.path.join(env.salt_roots, 'salt'),
        'pillar_root': os.path.join(env.salt_roots, 'pillar'),
    }
    upload_template(
        filename='templates/minion',
        destination=MINION_CONFIG,
        context=context,
        use_jinja=True
    )


def provision():
    """
    Calls Salt hightstate on the remote server.
    """
    run('salt-call --local state.highstate -l debug')


@task
def deploy():
    bootstrap_salt()
    sync_salt_roots()
    write_salt_minion_config()
    provision()
