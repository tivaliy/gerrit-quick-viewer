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

from flask import Blueprint, current_app, flash, render_template, request, \
    redirect, url_for

from gerritclient import client
from gerritclient import error as client_error

from gerritviewer import common

plugins = Blueprint('plugins', __name__)


@plugins.route('/plugins', methods=['GET', 'POST'])
@plugins.route('/plugins/<plugin_id>')
def fetch(plugin_id=None):
    action = request.args.get('action')
    gerrit_plugins, plugin = None, None
    plugin_client = client.get_client('plugin',
                                      connection=common.get_connection())
    plugin_actions = {'enable': plugin_client.enable,
                      'disable': plugin_client.disable,
                      'reload': plugin_client.reload}
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
                return redirect(url_for('plugins.fetch',
                                        plugin_id=plugin_id))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('plugins/plugins.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='plugins',
                           entries=gerrit_plugins,
                           entry_item=plugin,
                           entry_item_name=plugin['id'] if plugin else None)


@plugins.route('/plugins/install', methods=['GET', 'POST'])
def install():
    if request.method == 'POST':
        plugin_client = client.get_client('plugin',
                                          connection=common.get_connection())
        filename = request.files['file']
        url_path = request.form['plugin_url']
        if bool(url_path) == bool(filename):
            flash('Either URL or path to JAR-plugin file must be specified.',
                  category='error')
        else:
            plugin_name, source_type, value = None, None, None
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
                if plugin_name:
                    resp = plugin_client.install(plugin_name,
                                                 source_type,
                                                 value)
                    msg = "Start installing '{0}' plugin.".format(resp['id'])
                    flash(msg, category='note')
                    return redirect('plugins/{0}'.format(resp['id']))
            except (requests.ConnectionError, client_error.HTTPError) as error:
                current_app.logger.error(error)
                flash(error, category='error')
    return render_template('plugins/install.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version())
