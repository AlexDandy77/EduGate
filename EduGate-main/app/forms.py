from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class AddStudentForm(FlaskForm):
    user_id = IntegerField('User ID', validators=[DataRequired()])
    class_id = IntegerField('Class ID', validators=[DataRequired()])
    parent_id = IntegerField('Parent ID', validators=[DataRequired()])
    uid = StringField('UID', validators=[DataRequired()])
    submit = SubmitField('Add Student')
