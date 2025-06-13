from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, StringField, SubmitField
from app.dash.forms import SelectPickerWidget

class ClipFilterForm(FlaskForm):
    category = SelectField('Category', coerce=int)
    theme = SelectMultipleField('Theme', coerce=int)
    subject = SelectMultipleField('Subject', coerce=int, widget=SelectPickerWidget())
    search = StringField('Text Filter')
    filter = SubmitField('Apply')
    clear = SubmitField('Clear')