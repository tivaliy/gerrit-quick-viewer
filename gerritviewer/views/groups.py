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

from flask import Blueprint, flash, redirect, render_template, request, \
    session, current_app, Markup

from gerritviewer import common
from gerritclient import client
from gerritclient import error as client_error

groups = Blueprint('groups', __name__)


@groups.route('/groups', methods=['GET', 'POST'])
@groups.route('/groups/<group_id>')
def list_groups(group_id=None):
    action = request.args.get('action')
    gerrit_groups, group, group_name = None, {}, None
    group_client = client.get_client('group',
                                     connection=common.get_connection())
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
                actions = {'delete': group_client.delete_members,
                           'exclude': group_client.exclude}
                attribute = [request.args.get('member') or
                             request.args.get('group')]
                actions[action](group_id, attribute)
                flash(Markup("<strong>'{}'</strong> was successfully "
                             "{}d from <strong>'{}'</strong> group"
                             "".format(attribute[0], action, group['name'])),
                      category='note')
                return redirect('groups/{0}?details=1'.format(group_id))
        if group_name:
            response = group_client.create(group_name)
            flash(Markup("Group <strong>'{0}'</strong> was successfully "
                  "created.".format(response['name'])), category='note')
            return redirect('groups/{0}'.format(response['group_id']))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('groups.html',
                           username=session.get('username'),
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='groups',
                           entries=gerrit_groups,
                           entry_item=group,
                           entry_item_name=group.get('name'))
