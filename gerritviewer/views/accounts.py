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
    request, redirect, url_for

from gerritclient import client
from gerritclient import error as client_error

from gerritviewer import common
from .forms import QueryUserAccountForm
from .forms import CreateUserAccountForm

accounts = Blueprint('accounts', __name__)


@accounts.route('/accounts', methods=['GET', 'POST'])
def fetch():
    form = QueryUserAccountForm()
    gerrit_accounts = None
    account_client = client.get_client('account',
                                       connection=common.get_connection())
    try:
        if form.validate_on_submit():
            gerrit_accounts = account_client.get_all(
                form.query_string.data, detailed=form.details.data)
            flash(Markup("Search results for <strong>'{}'</strong>: {}".format(
                    form.query_string.data,
                    "Nothing Found" if not gerrit_accounts else '')),
                  category='note')
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('accounts/accounts.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='accounts',
                           entries=gerrit_accounts,
                           form=form)


@accounts.route('/accounts/<account_id>', methods=['GET', 'POST'])
def fetch_single(account_id=None):
    account = {}
    account_client = client.get_client('account',
                                       connection=common.get_connection())
    try:
        account = account_client.get_by_id(
            account_id, detailed=request.args.get('details', False))
        account['is_active'] = account_client.is_active(account_id)
        action = request.args.get('action')
        if action:
            account_actions = {'enable': account_client.enable,
                               'disable': account_client.disable}
            account_actions[action](account_id)
            flash(Markup("Account with <strong>ID={}</strong> was "
                         "successfully <strong>{}d</strong>".format(
                          account_id, action)), category='note')
            return redirect(url_for('accounts.fetch_single',
                                    account_id=account_id))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('accounts/single.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='accounts',
                           entry_item=account,
                           entry_item_name=account.get('name'))


@accounts.route('/accounts/create', methods=['GET', 'POST'])
def create():
    form = CreateUserAccountForm()
    if form.validate_on_submit():
        account_client = client.get_client('account',
                                           connection=common.get_connection())
        data = {k: v for k, v in (('username', form.username.data),
                                  ('name', form.fullname.data),
                                  ('email', form.email.data)) if v}
        try:
            response = account_client.create(form.username.data, data=data)
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
                           gerrit_version=common.get_version(),
                           form=form)
