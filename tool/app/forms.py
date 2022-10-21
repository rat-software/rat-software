from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField,\
                    BooleanField, SelectMultipleField, widgets, FieldList,\
                    FormField, RadioField, IntegerField, DecimalField,\
                    IntegerRangeField, PasswordField, EmailField,\
                    validators, HiddenField
from flask_wtf.file import FileField


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class StudyForm(FlaskForm):
    id = HiddenField("Study ID", default=0)
    name = StringField("Study name", [validators.InputRequired("Input required.")])
    description = TextAreaField("Description")
    type = SelectField("Study type", coerce=int)
    imported = BooleanField("Import own search results", default=False)
    imported_data = FileField("Add own search results (csv)")
    search_engines = MultiCheckboxField("Select search engines", coerce=int)
    result_type = SelectField("Select result types", choices=[(1, "Organic Results"),
                                                               (2, "Snippets"),
                                                               (3, "Universal Search Results"),
                                                               (4, "Advertisements")], coerce=int)
    queries = TextAreaField("Queries (use new line for each query; max. 3 Queries)")
    query_list = FileField("List of queries (csv)")
    result_count = IntegerField("Number of results to collect", default=10)
    submit = SubmitField("Create study")


class MonitoringForm(FlaskForm):
    name = StringField("Monitoring name")
    description = TextAreaField("Monitoring description")
    queries = TextAreaField("Queries (use new line for each query)")
    countries = MultiCheckboxField("Select countries", coerce=int)
    result_count = IntegerField("Number of results to collect")
    result_type = SelectField("Select result types", choices=[(2, "Snippets")], coerce=int)
    interval_frequency = SelectField("Frequency", choices=[(1, "once"), (2, "twice")])
    interval_mode = SelectField("Mode",
                                choices=[(1, "daily"), (2, "weekly"), (3, "monthly")],
                                coerce=int)
    submit = SubmitField("Create monitoring")


class ConfirmationForm(FlaskForm):
    data = HiddenField("Data")
    submit = SubmitField("Confirm")

class AnswerOptions(FlaskForm):
    value = StringField("Value")
    label = StringField("Label")


class RangeOptions(FlaskForm):
    start = IntegerField("Start")
    stop = IntegerField("Stop")
    step = DecimalField("Steps")


class QuestionForm(FlaskForm):
    q_type = SelectField("Question type")
    text = StringField("Question")
    position = IntegerField("Question number")
    interval = RadioField("Display question for...", choices=[(1, "Each Result"), (10, "Every 10 Results")], coerce=int)
    description = StringField("Description (optional)")
    options = FieldList(FormField(AnswerOptions), min_entries=2, label="Answer Options")
    ranges = FieldList(FormField(RangeOptions), min_entries=1, label="Range Options")
    submit = SubmitField("Create question")


class AnswerForm(FlaskForm):
    short_text = StringField("Answer")
    long_text = TextAreaField("Answer")
    true_false = RadioField("Answer", coerce=int)
    likert_scale = RadioField("Answer", coerce=int)
    multiple_choice = MultiCheckboxField("Answer", coerce=int)
    scale_number = IntegerRangeField("Answer")
    submit = SubmitField("Next")
    skip = SubmitField("Skip")


class EvaluationForm(FlaskForm):
    status = RadioField("Status", choices=[(1, "OK"), (0, "Not OK")], coerce=int)
    comment = TextAreaField("Comment")
    submit = SubmitField("Submit")


class JoinForm(FlaskForm):
    new = SubmitField("New")
    returning = SubmitField("Returning")


class ParticipantLogInForm(FlaskForm):
    username = StringField("Username")
    password = PasswordField("Code")
    submit = SubmitField("Log in")


class ExportForm(FlaskForm):
    tables = RadioField("Select data to export:", coerce=int)
    submit = SubmitField("Generate Excel")


class ContactForm(FlaskForm):
    name = StringField("Name")
    email = EmailField("E-Mail")
    message = TextAreaField("Message")
    submit = SubmitField("Send")
