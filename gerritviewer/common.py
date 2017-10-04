import requests

from flask import current_app, flash, session

from gerritclient import client
from gerritclient import error as client_error


def get_gerrit_url():
    return session.get('gerrit_url') or current_app.config.get('GERRIT_URL')


def get_connection():
    return client.connect(get_gerrit_url(),
                          auth_type=session.get('auth_type'),
                          username=session.get('username'),
                          password=session.get('password'))


def get_version(url=None):
    version = None
    gerrit_url = url or get_gerrit_url()
    try:
        version = client.get_client(
            'server',
            connection=client.connect(gerrit_url)
        ).get_version()
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash("Can't establish connection with Gerrit server at '{0}'. "
              "See logs for more details".format(gerrit_url), category='error')
    return version
