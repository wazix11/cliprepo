from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError

class ClipFilterForm(FlaskForm):
    category = SelectField('Category', coerce=int)
    theme = SelectField('Theme', coerce=int)
    featured = SelectMultipleField('Featured', coerce=int)
    text_filter = StringField('Text Filter')
    filter = SubmitField('Filter')