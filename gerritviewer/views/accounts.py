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

from flask import Blueprint, current_app, flash, Markup, render_template, \
    request, redirect

from gerritclient import client
from gerritclient import error as client_error

from gerritviewer import common

accounts = Blueprint('accounts', __name__)


@accounts.route('/accounts', methods=['GET', 'POST'])
@accounts.route('/accounts/<account_id>', methods=['GET', 'POST'])
def fetch(account_id=None):
    action = request.args.get('action')
    gerrit_accounts, account = None, {}
    account_client = client.get_client('account',
                                       connection=common.get_connection())
    account_actions = {'enable': account_client.enable,
                       'disable': account_client.disable}
    try:
        if request.method == 'POST':
            if 'search_form' in request.form:
                detailed = True if request.form.getlist('details') else False
                gerrit_accounts = account_client.get_all(
                    request.form['query_string'], detailed=detailed)
                flash(Markup(
                    "Search results for <strong>'{}'</strong>: {}".format(
                        request.form['query_string'],
                        "Nothing Found" if not gerrit_accounts else '')),
                      category='note')
        if account_id:
            account = account_client.get_by_id(
                account_id, detailed=request.args.get('details', False))
            account['is_active'] = account_client.is_active(account_id)
            if action:
                account_actions[action](account_id)
                flash(Markup("Account with <strong>ID={}</strong> was "
                             "successfully <strong>{}d</strong>".format(
                              account_id, action)), category='note')
                return redirect('accounts/{0}'.format(account_id))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('accounts/accounts.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='accounts',
                           entries=gerrit_accounts,
                           entry_item=account,
                           entry_item_name=account.get('name'))


@accounts.route('/accounts/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        account_client = client.get_client('account',
                                           connection=common.get_connection())
        data = {k: v
                for k, v in (('username', request.form['username']),
                             ('name', request.form['fullname']),
                             ('email', request.form['email'])) if v}
        try:
            response = account_client.create(request.form['username'],
                                             data=data)
            msg = Markup("A new user account '<strong>{0}</strong>' "
                         "with ID={1} was successfully created.".format(
                          response['username'], response['_account_id']))
            flash(msg, category='note')
            return redirect('accounts/{0}'.format(response['_account_id']))
        except (requests.ConnectionError, client_error.HTTPError) as error:
                current_app.logger.error(error)
                flash(error, category='error')
    return render_template('accounts/create.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version())
