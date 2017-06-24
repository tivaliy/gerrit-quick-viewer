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
     url_for, Markup
from gerritclient import client
from gerritclient import error as client_error


GERRIT_URL = 'http://ci.infra.local/gerrit'

app = Flask(__name__)
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='development key'
))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                           gerrit_url=GERRIT_URL,
                           gerrit_version=get_version()), 404


@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html',
                           username=username,
                           gerrit_url=GERRIT_URL,
                           gerrit_version=get_version())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not request.form['username']:
            flash('Invalid Username', category='error')
        elif not request.form['password']:
            flash('Password field cannot be empty', category='error')
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            session['password'] = request.form['password']
            flash(Markup("You were logged in as <strong>'{0}'</strong> "
                         "user").format(session['username']), category='note')
            return redirect(url_for('index'))
    return render_template('login.html',
                           gerrit_url=GERRIT_URL,
                           gerrit_version=get_version())


@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out', category='note')
    return redirect(url_for('index'))


@app.route('/groups', methods=['GET', 'POST'])
@app.route('/groups/<group_id>')
def groups(group_id=None):
    action = request.args.get('action')
    gerrit_groups, group, group_name = None, {}, None
    connection = client.connect(GERRIT_URL,
                                username=session.get('username'),
                                password=session.get('password'))
    group_client = client.get_client('group', connection=connection)
    if request.method == 'POST':
        group_name = request.form['group_name']
        if not group_name:
            flash('Name of group must be specified.', category='error')
    try:
        gerrit_groups = group_client.get_all()
        if group_id:
            group = group_client.get_by_id(
                group_id,
                detailed=request.args.get('details')
            )
            if action:
                group_client.delete_members(group_id,
                                            [request.args.get('member')])
                flash(Markup("User <strong>'{}'</strong> was successfully "
                             "removed from <strong>'{}'</strong> group"
                             "".format(request.args.get('member'),
                                       group['name'])), category='note')
                return redirect('groups/{0}?details=1'.format(group_id))
        if group_name:
            response = group_client.create(group_name)
            flash("Group '{0}' was successfully "
                  "created.".format(response['name']), category='note')
            return redirect('groups/{0}'.format(response['group_id']))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        app.logger.error(error)
        flash(error, category='error')
    return render_template('groups.html',
                           username=session.get('username'),
                           gerrit_url=GERRIT_URL,
                           gerrit_version=get_version(),
                           entry_category='groups',
                           entries=gerrit_groups,
                           entry_item=group,
                           entry_item_name=group.get('name'))


@app.route('/plugins', methods=['GET', 'POST'])
@app.route('/plugins/<plugin_id>')
def plugins(plugin_id=None):
    action = request.args.get('action')
    gerrit_plugins, plugin = None, None
    plugin_name, source_type, value = None, None, None
    connection = client.connect(GERRIT_URL,
                                username=session.get('username'),
                                password=session.get('password'))
    plugin_client = client.get_client('plugin', connection=connection)
    plugin_actions = {'enable': plugin_client.enable,
                      'disable': plugin_client.disable,
                      'reload': plugin_client.reload}
    if request.method == 'POST':
        filename = request.files['file']
        url_path = request.form['plugin_url']
        if bool(url_path) == bool(filename):
            flash('Either URL or path to JAR-plugin file must be specified.',
                  category='error')
        else:
            if filename:
                if filename.filename[-3:].lower() != 'jar':
                    flash('Plugin file must be of JAR type.', category='error')
                else:
                    source_type, value = 'file', filename.stream.read()
                    plugin_name = filename.filename
            if url_path:
                    source_type, value = 'url', url_path
                    plugin_name = url_path.split("/")[-1]
    try:
        gerrit_plugins = plugin_client.get_all(detailed=True)
        if plugin_id:
            plugin = plugin_client.get_by_id(plugin_id)
            if action:
                plugin_actions[action](plugin_id)
                action = ('{}d'.format(action)
                          if action[-1] == 'e' else '{}ed'.format(action))
                msg = "Plugin '{0}' was successfully {1}.".format(plugin_id,
                                                                  action)
                flash(msg, category='note')
                return redirect(url_for('plugins', plugin_id=plugin_id))
        if plugin_name:
            response = plugin_client.install(plugin_name, source_type, value)
            flash("Start installing '{0}' plugin.".format(response['id']),
                  category='note')
            return redirect('plugins/{0}'.format(response['id']))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        app.logger.error(error)
        flash(error, category='error')
    return render_template('plugins.html',
                           username=session.get('username'),
                           gerrit_url=GERRIT_URL,
                           gerrit_version=get_version(),
                           entry_category='plugins',
                           entries=gerrit_plugins,
                           entry_item=plugin,
                           entry_item_name=plugin['id'] if plugin else None)


def get_version():
    version = None
    try:
        version = client.get_client(
            'config', connection=client.connect(GERRIT_URL)).get_version()
    except requests.ConnectionError as e:
        app.logger.error(e.message)
        flash(e, category='error')
    return version


if __name__ == '__main__':
    app.run()
