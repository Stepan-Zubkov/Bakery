from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Length, Email, DataRequired


class RegistrationForm(FlaskForm):
    email = EmailField('Email', validators=[
        Email('Incorrect email'),
        Length(min=10, max=100, message='Incorrect length'),
        DataRequired()
    ])
    password = PasswordField('Password', validators=[
        Length(min=4, max=100, message='Incorrect length'),
        DataRequired()
    ])
    first_name = StringField('First name', validators=[
        Length(min=2, max=50, message='Incorrect length'),
        DataRequired()
    ])
    last_name = StringField('Last name', validators=[
        Length(min=2, max=50, message='Incorrect length'),
        DataRequired()
    ])
    address = StringField('Address', validators=[
        Length(min=-1, max=100, message='Incorrect length'),
    ])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Create account')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[
        Email('Incorrect email'),
        Length(min=10, max=100, message='Incorrect length'),
        DataRequired()
    ])
    password = PasswordField('Password', validators=[
        Length(min=4, max=100, message='Incorrect length'),
        DataRequired()
    ])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')
