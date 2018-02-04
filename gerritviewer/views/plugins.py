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

import os
import requests

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from flask import Blueprint, current_app, flash, Markup, render_template, \
    request, redirect, url_for

from gerritclient import client
from gerritclient import error as client_error

from gerritviewer import common
from .forms import InstallPluginForm

plugins = Blueprint('plugins', __name__)


@plugins.route('/plugins')
@plugins.route('/plugins/<plugin_id>')
def fetch(plugin_id=None):
    action = request.args.get('action')
    gerrit_plugins = None
    plugin_client = client.get_client('plugin',
                                      connection=common.get_connection())
    try:
        if plugin_id:
            plugin = plugin_client.get_by_id(plugin_id)
            if action:
                plugin_actions = {'enable': plugin_client.enable,
                                  'disable': plugin_client.disable,
                                  'reload': plugin_client.reload}
                plugin_actions[action](plugin_id)
                action = ('{}d'.format(action)
                          if action[-1] == 'e' else '{}ed'.format(action))
                msg = Markup("Plugin <strong>'{0}'</strong> was successfully "
                             "<strong>{1}</strong>.".format(plugin_id, action))
                flash(msg, category='note')
                return redirect(url_for('plugins.fetch',
                                        plugin_id=plugin_id))
            return render_template('plugins/single.html',
                                   gerrit_url=common.get_gerrit_url(),
                                   gerrit_version=common.get_version(),
                                   entry_category='plugins',
                                   entry_item_name=plugin['id'],
                                   entry_item=plugin)
        else:
            gerrit_plugins = plugin_client.get_all(detailed=True)
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('plugins/plugins.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='plugins',
                           entries=gerrit_plugins)


@plugins.route('/plugins/install', methods=['GET', 'POST'])
def install():
    form = InstallPluginForm()
    if form.validate_on_submit():
        plugin_client = client.get_client('plugin',
                                          connection=common.get_connection())
        plugin_name, source_type, value = None, None, None
        if form.file.data:
            source_type, value = 'file', form.file.data.read()
            plugin_name = form.file.data.filename
        if form.plugin_url.data:
            source_type, value = 'url', form.plugin_url.data
            plugin_name = os.path.basename(
                urlparse.urlsplit(form.plugin_url.data).path)
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
                           gerrit_version=common.get_version(),
                           form=form)
