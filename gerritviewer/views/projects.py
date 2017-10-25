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

from flask import Blueprint, current_app, flash, render_template, request

from gerritclient import client
from gerritclient import error as client_error

from gerritviewer import common

projects = Blueprint('projects', __name__)


@projects.route('/projects')
@projects.route('/projects/<path:project_name>')
def list_projects(project_name=None):
    skip = request.args.get('skip')
    gerrit_projects, project = None, {}
    project_client = client.get_client('project',
                                       connection=common.get_connection())
    try:
        gerrit_projects = project_client.get_all(is_all=True, limit=25,
                                                 description=True, skip=skip)
        if project_name:
            project = project_client.get_by_name(project_name)
            return render_template('projects/single.html',
                                   gerrit_url=common.get_gerrit_url(),
                                   gerrit_version=common.get_version(),
                                   entry_category='projects',
                                   entry_item=project,
                                   entry_item_name=project.get('name'))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('projects/projects.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='projects',
                           entries=gerrit_projects)
