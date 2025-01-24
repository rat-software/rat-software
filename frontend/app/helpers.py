from . import app, db
from .forms import AnswerForm
from app.models import Option
from markupsafe import Markup
from crontab import CronTab

def get_options(question):
    """
    Retrieves and formats answer options for a given question based on its type.

    Args:
        question (Question): The question object for which to get options.

    Returns:
        AnswerForm: A form with fields populated based on the question's options and type.
    """
    form = AnswerForm()
    display = question.questiontype.display  # Get the display type of the question
    choices = []
    options = Option.query.filter(Option.question == question)\
                          .order_by(Option.position).all()  # Fetch options related to the question

    if display in ("true_false", "likert_scale", "multiple_choice"):
        # Prepare choices for question types that use predefined options
        for o in options:
            choices.append((o.value, o.label))

        if display == "true_false":
            form.true_false.choices = choices  # Set choices for True/False type questions

        elif display == "likert_scale":
            # Format choices for Likert scale with spacing
            choices = [(c[0], Markup(f"{c[0]}&nbsp;&nbsp;{c[1]}")) for c in choices]
            form.likert_scale.choices = choices  # Set choices for Likert scale type questions

        elif display == "multiple_choice":
            form.multiple_choice.choices = choices  # Set choices for Multiple Choice type questions

    elif display == "scale_number":
        # Prepare arguments for scale number type questions
        args = {o.label: o.value for o in options}
        form.scale_number.render_kw = args  # Set render keyword arguments for scale number field

    return form


def create_monitoring(id, form):
    """
    Creates a cron job for monitoring based on the provided form data.

    Args:
        id (int): The ID of the monitoring task.
        form (MonitoringForm): The form containing the scheduling details.
    """
    # Cron job lookup dictionary for scheduling intervals
    cron_lookup = {
        '1_1': '0 0 * * *',  # Once per day
        '2_1': '0 */12 * * *',  # Twice per day
        '1_2': '0 0 * * 1',  # Once per week
        '2_2': '0 0 * * 1,5',  # Twice per week
        '1_3': '0 0 1 * *',  # Once per month
        '2_3': '0 0 */15 * *'  # Twice per month
    }

    # Construct the cron job key from form data
    f = str(form.interval_frequency.data)
    m = str(form.interval_mode.data)
    key = '_'.join([f, m])

    # Determine the cron schedule based on the key
    timer = cron_lookup.get(key, '0 0 * * *')  # Default to daily if key is not found

    cmd = "python test.py"
    arg = str(id)
    cmd_full = f'{cmd} {arg}'

    # Schedule the cron job
    cron = CronTab(user=True)  # Ensure the CronTab instance is created for the current user
    job = cron.new(command=cmd_full)
    job.setall(timer)
    cron.write()


def percentage_calc(value, total_value, type):
    """
    Calculates the percentage of a given value relative to a total value.

    Args:
        value (float): The value to calculate the percentage of.
        total_value (float): The total value used for percentage calculation.
        type (str): The format of the result - "int", "float", or "str".

    Returns:
        str or float: The calculated percentage in the specified format.
    """
    if total_value > 0:
        ratio = value / total_value
        if type == "int":
            result = round(ratio * 100)  # Convert to integer percentage
        elif type == "float":
            result = ratio  # Return as float percentage
        elif type == "str":
            result = f"{round(ratio * 100)} %"  # Return as string with percentage sign
    else:
        result = "-"  # Return "-" if total value is 0

    return result
