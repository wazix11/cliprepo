from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, ValidationError
from wtforms.widgets import ColorInput

class deleteForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Delete')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class clipForm(FlaskForm):
    title_override = StringField('Title Override')
    notes = TextAreaField('Notes')
    category = SelectField('Category', coerce=int)
    status = SelectField('Status', coerce=int)
    themes = SelectMultipleField('Themes', coerce=int)
    subjects = SelectMultipleField('Subjects', coerce=int)
    save = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class categoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    save = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class themeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    save = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class subjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    subtext = StringField('Subtext') # This should probably be a SelectField with set values
    keywords = TextAreaField('Keywords')
    public = BooleanField('Public')
    notes = TextAreaField('Notes')
    save = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class subjectCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    save = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class userForm(FlaskForm):
    rank = SelectField('Rank', coerce=int)
    contributions = StringField('Contributions')
    enabled = BooleanField('Login Enabled')
    notes = TextAreaField('Notes')
    save = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class statusLabelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    status_type = SelectField('Status Type', choices=['', 'Visible', 'Pending', 'Hidden'], validators=[DataRequired()])
    color = StringField('Color', widget=ColorInput())
    notes = TextAreaField('Notes')
    save = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})