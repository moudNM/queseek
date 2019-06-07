from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, validators, SelectField, HiddenField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Login')

    def validate_username(self, username):
        pass

    def validate_email(self, email):
        pass


class SignUpForm(FlaskForm):
    email = StringField('Email')
    username = StringField('Username')
    password = PasswordField('New Password', [
        validators.DataRequired()
    ])
    confirm = PasswordField('Repeat Password', [
        validators.DataRequired()
    ])
    submit = SubmitField('Sign Up')
    update = SubmitField('Update')


class QuestForm(FlaskForm):

    type = SelectField("Type: ", choices=[(0, "Hero Quest (Lost an item)"), (1, "Side Quest (Errand)")], default=0)
    item = StringField('Item:', [
        validators.DataRequired()
    ])
    location = StringField('Location:', [
        validators.DataRequired()
    ])
    description = StringField('Description:', widget=TextArea())
    submit = SubmitField('Submit')


class SeekForm(FlaskForm):

    item = StringField('Item:', [
        validators.DataRequired()
    ])
    location = StringField('Location:', [
        validators.DataRequired()
    ])
    description = StringField('Description:', widget=TextArea())
    submit = SubmitField('Submit')


class QuestCommentsForm(FlaskForm):
    questId = HiddenField('questId:')
    userId = HiddenField('userId:')
    is_creator = HiddenField('is_creator:')
    description = StringField('Description:', widget=TextArea())
    submit = SubmitField('Submit')


class SeekCommentsForm(FlaskForm):
    seekId = HiddenField('seekId:')
    userId = HiddenField('userId:')
    is_creator = HiddenField('is_creator:')
    description = StringField('Description:', widget=TextArea())
    submit = SubmitField('Submit')