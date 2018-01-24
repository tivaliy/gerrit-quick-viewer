from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired


class QueryUserAccountForm(FlaskForm):
    query_string = StringField('Query string:', validators=[DataRequired()])
    details = BooleanField('Show details', default='checked')


class CreateUserAccountForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    fullname = StringField('Full Name:')
    email = StringField('e-mail:')


class CreateGroupForm(FlaskForm):
    group_name = StringField(validators=[DataRequired()])
