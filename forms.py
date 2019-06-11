from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo 
from pprint import pprint
import webbrowser



###################
###### FORMS ######
###################
class LoginForm(FlaskForm):
    username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:')
    submit = SubmitField("Login")

class newUserForm(FlaskForm):
	submit = SubmitField("Confirm")

class SearchForm(FlaskForm):
    search_term = StringField("Enter search term",validators=[Required()])
    myChoices   = [('1','1'),('5','5'),('10','10'),('20','20'),('30','30'),('50','50'),('100','100'),('1000','1000')] 
    results_num = SelectField("Result number", choices = myChoices, default=10)
    submit = SubmitField()

class SelectFoodForm(FlaskForm):
    select = SubmitField('Calculate index')
    favorite = SubmitField('★')
