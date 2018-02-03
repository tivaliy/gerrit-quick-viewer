import os

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, FileField
from wtforms.validators import DataRequired, Email, ValidationError


class QueryUserAccountForm(FlaskForm):
    query_string = StringField('Query string:', validators=[DataRequired()])
    details = BooleanField('Show details', default='checked')


class CreateUserAccountForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    fullname = StringField('Full Name:')
    email = StringField('e-mail:', validators=[Email()])


class CreateGroupForm(FlaskForm):
    group_name = StringField(validators=[DataRequired()])


class ConfigureSettingsForm(FlaskForm):
    gerrit_url = StringField(validators=[DataRequired()])


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
