from flask.ext.wtf import Form
from wtforms import TextField, DateField,PasswordField, BooleanField,validators,SelectField,RadioField
from models import Monkey


class RegistrationForm(Form):
    name = TextField('Your name', [validators.InputRequired()])
    email = TextField('Email Address', [validators.InputRequired(), validators.Email()])
    dob = DateField('Date of Birth', [validators.InputRequired()])
    username = TextField('Username', [validators.InputRequired()])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        
    def validate(self):
        if not Form.validate(self):
            return False
     
        monkey = Monkey.query.filter_by(username = self.username.data).first()
        if monkey:
          self.username.errors.append("That username is already taken")
          return False
        else:
            return True
    
class LoginForm(Form):
    username = TextField('Username', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired()])
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    
class EditForm(Form):
    name = TextField('Your name', [validators.InputRequired()])
    email = TextField('Email Address', [validators.InputRequired(), validators.Email()])
    dob = DateField('Date of Birth', [validators.InputRequired()])

class SearchForm(Form):
    search = TextField('Monkey Search', [validators.InputRequired()])


    
    
