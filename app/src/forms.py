from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from .models import User, Environment

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different username.')

class EnvironmentForm(FlaskForm):
    name = StringField('Environment Name', validators=[DataRequired(), Length(min=1, max=100)])
    submit = SubmitField('Create Environment')
    
    def validate_name(self, name):
        from flask_login import current_user
        environment = Environment.query.filter_by(name=name.data, created_by=current_user.id).first()
        if environment:
            raise ValidationError('Environment name already exists. Please choose a different name.')

class CSVUploadForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'Only CSV files are allowed!')
    ])
    submit = SubmitField('Upload CSV')

class RemarksForm(FlaskForm):
    remarks = TextAreaField('Remarks', validators=[Length(max=1000)])
    submit = SubmitField('Update Remarks')

class UserApprovalForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Approve')

class UserRejectionForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Reject')

class RoleAssignmentForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Update Role')