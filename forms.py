from flask.ext.wtf import Form
from wtforms import validators
from wtforms import TextField, PasswordField, DateTimeField, TextAreaField, SubmitField

class LoginForm(Form):
    username = TextField('username', validators = [validators.Required()])
    password = PasswordField('password', validators = [validators.Required()])

class EditForm(Form):
    recorded = DateTimeField('recorded', format="%d.%m.%Y %H:%M", validators = [validators.Required()])
    comment = TextAreaField('comment')
    submit = SubmitField('Abschicken')
