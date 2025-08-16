from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    user_id = StringField('User ID', validators=[DataRequired()])
    designation = SelectField('Designation', choices=[
    ('Admin', 'Admin'),
    ('Warehouse', 'Warehouse'),
    ('QC', 'QC'),
    ('Production', 'Production'),
    ('QA', 'QA')
])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
