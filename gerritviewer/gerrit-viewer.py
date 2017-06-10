#
#    Copyright 2017 Vitalii Kulanov
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import requests

from flask import Flask, flash, render_template, request, redirect, session, \
     url_for
from gerritclient import client
from gerritclient import error as client_error


GERRIT_URL = 'http://ci.infra.local/gerrit'

app = Flask(__name__)
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='development key'
))


@app.route('/')
def index():
    username = session.get('username')
    gerrit_version, error = get_version()
    return render_template('index.html',
                           error=error,
                           username=username,
                           gerrit_url=GERRIT_URL,
                           gerrit_version=gerrit_version)


@app.route('/login', methods=['GET', 'POST'])
def login():
    gerrit_version, error = get_version()
    if request.method == 'POST':
        if not request.form['username']:
            error = 'Invalid Username'
        elif not request.form['password']:
            error = 'Password field cannot be empty'
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            session['password'] = request.form['password']
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html',
                           error=error,
                           gerrit_url=GERRIT_URL,
                           gerrit_version=gerrit_version)


@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out')
    return redirect(url_for('index'))


@app.route('/plugins')
@app.route('/plugins/<plugin_id>')
def plugins(plugin_id=None):
    gerrit_version, error = get_version()
    gerrit_plugins, plugin = None, None
    username = session.get('username')
    password = session.get('password')
    connection = client.connect(GERRIT_URL,
                                username=username,
                                password=password)
    plugin_client = client.get_client('plugin', connection=connection)
    try:
        gerrit_plugins = plugin_client.get_all()
        if plugin_id:
            plugin = plugin_client.get_by_id(plugin_id)
    except (requests.ConnectionError, client_error.HTTPError) as error:
        app.logger.error(error)
    return render_template('plugin.html',
                           error=error,
                           username=username,
                           gerrit_url=GERRIT_URL,
                           gerrit_version=gerrit_version,
                           entry_category='plugins',
                           entries=gerrit_plugins,
                           entry_item=plugin,
                           entry_item_name=plugin['id'] if plugin else None)


def get_version():
    try:
        version = client.get_client(
            'config', connection=client.connect(GERRIT_URL)).get_version()
        return version, None
    except requests.ConnectionError as e:
        app.logger.error(e)
    return None, e


if __name__ == '__main__':
    app.run()
