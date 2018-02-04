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

from flask import Blueprint, flash, Markup, render_template, request, \
    redirect, session, url_for

from gerritviewer import common
from .forms import ConfigureSettingsForm, LoginForm

home = Blueprint('home', __name__)


@home.route('/')
def index():
    return render_template('index.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version())


@home.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session['logged_in'] = True
        session['username'] = form.username.data
        session['password'] = form.password.data
        session['auth_type'] = form.auth_type.data
        flash(Markup("You were logged in as <strong>'{0}'</strong> "
                     "user").format(session['username']), category='note')
        return redirect(url_for('home.index'))
    return render_template('login.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='Sign In',
                           form=form)


@home.route('/logout')
def logout():
    session.clear()
    flash('You were logged out.', category='note')
    return redirect(url_for('home.index'))


@home.route('/settings', methods=['GET', 'POST'])
def settings():
    form = ConfigureSettingsForm()
    if form.validate_on_submit():
        if common.get_version(form.gerrit_url.data):
            session['gerrit_url'] = form.gerrit_url.data
            flash(Markup("Gerrit server URL path '<strong>{0}</strong>' was "
                         "successfully saved".format(session['gerrit_url'])),
                  category='note')
            return redirect(url_for('home.index'))
    return render_template('settings.html',
                           gerrit_url=common.get_gerrit_url(),
                           gerrit_version=common.get_version(),
                           entry_category='Settings',
                           form=form)
