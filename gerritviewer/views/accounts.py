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
from .forms import CreateUserAccountForm, EditContactInfoForm, \
    QueryUserAccountForm

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


@accounts.route('/accounts/<account_id>')
def fetch_single(account_id):
    account = {}
    account_client = client.get_client('account',
                                       connection=common.get_connection())
    try:
        account = account_client.get_by_id(
            account_id, detailed=request.args.get('details', False))
        account['is_active'] = account_client.is_active(account_id)
        account['membership'] = account_client.get_membership(account_id)
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
    return render_template('accounts/profile.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='accounts',
                           entry_item=account,
                           entry_item_name=account.get('name'))


@accounts.route('/accounts/contact/<account_id>', methods=['GET', 'POST'])
def edit_contact_info(account_id):
    form = EditContactInfoForm()
    account = {}
    account_client = client.get_client('account',
                                       connection=common.get_connection())
    try:
        account = account_client.get_by_id(account_id, detailed=False)
        current_status = get_account_status(account_id)
        if form.validate_on_submit():
            fullname, username = form.fullname.data, form.username.data
            status = form.status.data
            response = {}
            if account.get('name') != fullname:
                response['full name'] = account_client.set_name(account_id,
                                                                fullname)
            if username and account.get('username') != username:
                response['username'] = account_client.set_username(account_id,
                                                                   username)
            if status != current_status:
                response['status'] = account_client.set_status(account_id,
                                                               status) or ''
            if response:
                flash(Markup("The following parameters were successfully "
                             "updated: {0}".format(", ".join(
                              ":: ".join(_) for _ in response.items()))),
                      category='note')
            return redirect(url_for('accounts.fetch_single',
                                    account_id=account_id))
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('accounts/contacts.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='accounts',
                           entry_item=account,
                           entry_item_name=account.get('name'),
                           form=form)


@accounts.route('/accounts/ssh/<account_id>')
def ssh(account_id):
    account_client = client.get_client('account',
                                       connection=common.get_connection())
    account, ssh_keys = {}, []
    try:
        account = account_client.get_by_id(account_id, detailed=False)
        ssh_keys = account_client.get_ssh_keys(account_id)
    except (requests.ConnectionError, client_error.HTTPError) as error:
        current_app.logger.error(error)
        flash(error, category='error')
    return render_template('accounts/ssh.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='accounts',
                           entry_item=account,
                           entry_item_name=account.get('name'),
                           entries=ssh_keys)


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
            return redirect(url_for('accounts.fetch_single',
                                    account_id=response['_account_id']))
        except (requests.ConnectionError, client_error.HTTPError) as error:
                current_app.logger.error(error)
                flash(error, category='error')
    return render_template('accounts/create.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           form=form)


# Status of account is only available since gerrit 2.14,
# so we have to fetch it in a proper way for all versions
def get_account_status(account_id):
    account_client = client.get_client('account',
                                       connection=common.get_connection())
    try:
        current_status = account_client.get_status(account_id)
    except client_error.HTTPError:
        current_status = None
    return current_status
