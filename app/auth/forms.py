from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User
from flask_babel import lazy_gettext as _l


# form for user to login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField(_l('Keep me signed in '))
    submit = SubmitField(_l('Sign in'))


# form for user to register a new account
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 32),
        Regexp('^\w+$', 0, 'Username must contain only english letters, numbers, or underscores')])
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(1, 24), EqualTo('password_check', message='Passwords must match each other')])
    password_check = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField(_l('Sign up'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email has already been occupied')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('This username has already been occupied')


# form for user to reset their password
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[
        DataRequired(), Length(1, 24), EqualTo('password_check', message='Passwords must match each other')])
    password_check = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField(_l('Reset My Password'))


# form for users to apply for resetting their password
class ResetPasswordApplicationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField(_l('Reset My Password'))
