# Flask Forms used in the app

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField,\
                    BooleanField, SelectMultipleField, widgets, FieldList,\
                    FormField, RadioField, IntegerField, DecimalField,\
                    IntegerRangeField, PasswordField, EmailField,\
                    validators, HiddenField
from flask_wtf.file import FileField
from wtforms.widgets import TextArea

class StudyForm(FlaskForm):
    """
    Form for creating or editing a study.
    """
    id = HiddenField("Study ID", default=0)
    """
    Hidden field to store the study ID.
    """
    name = StringField("Study name", [validators.InputRequired("Input required.")])
    """
    Field for entering the study name. This field is required.
    """
    
class KeywordsForm(FlaskForm):
    """
    Form for entering keywords related to a study.
    """
    language_criterion = SelectField(u'Language', coerce=int)
    """
    Dropdown field for selecting a language criterion. The values are coerced to integers.
    """
    region_criterion = SelectField(u'Region', coerce=int)
    """
    Dropdown field for selecting a region criterion. The values are coerced to integers.
    """
    keywords = StringField(u'Text', widget=TextArea())
    """
    Field for entering keywords as a multi-line text. The TextArea widget is used for better readability.
    """
