import os

from flask_wtf import FlaskForm
from pkg_resources import parse_version
from wtforms import BooleanField, FileField, RadioField, StringField, \
    PasswordField
from wtforms.validators import DataRequired, Email, Optional, ValidationError

from gerritviewer import common


class QueryUserAccountForm(FlaskForm):
    query_string = StringField('Query string:', validators=[DataRequired()])
    details = BooleanField('Show details', default='checked')


class CreateUserAccountForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    fullname = StringField('Full Name:')
    email = StringField('e-mail:', validators=[Optional(), Email()])


class VersionCompatibility(object):
    """
    Validates Gerrit version compatibility.

    :param version: Gerrit version (as a string) to be compared
    :param message: Error message to raise in case of a validation error.
    """

    def __init__(self, version, message=None):
        self.message = message
        self.version = version

    def __call__(self, form, field):
        if field.data:
            curr_version = common.get_version()
            if parse_version(curr_version) <= parse_version(self.version):
                message = self.message
                if message is None:
                    message = field.gettext(
                        'This feature supports in Gerrit since version '
                        '{0}'.format(self.version)
                    )
                raise ValidationError(message)


class EditContactInfoForm(FlaskForm):
    fullname = StringField('Full Name:', validators=[DataRequired()])
    username = StringField('Username:')
    status = StringField('Status:', validators=[VersionCompatibility('2.14')])


class CreateGroupForm(FlaskForm):
    group_name = StringField(validators=[DataRequired()])


class ConfigureSettingsForm(FlaskForm):
    gerrit_url = StringField('Gerrit URL-path:', validators=[DataRequired()])


class JARFileRequired(object):

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if field.data:
            _, ext = os.path.splitext(field.data.filename)
            if ext.lower() != '.jar':
                raise ValidationError('Plugin file must be of JAR type.')


class InstallPluginForm(FlaskForm):
    plugin_url = StringField()
    file = FileField(validators=[JARFileRequired()])

    def validate(self):
        if not super(InstallPluginForm, self).validate():
            return False
        if not self.plugin_url.data and not self.file.data:
            msg = 'Either URL or path to JAR-plugin file must be specified.'
            self.plugin_url.errors.append(msg)
            return False
        return True


class LoginForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    auth_type = RadioField(choices=[('basic', 'HTTP Basic'),
                                    ('digest', 'HTTP Digest')],
                           default='basic')
