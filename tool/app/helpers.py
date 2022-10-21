from . import app, db
from .forms import AnswerForm
from app.models import Option
from flask import Markup

# gets and formats answer options for the different questiont types
# args: question
# returns AnswerForm with answer options formatted for the particular question type
def get_options(question):
    form = AnswerForm()
    display = question.questiontype.display
    choices = []
    options = Option.query.filter(Option.question == question)\
                          .order_by(Option.position)

    if display in ("true_false", "likert_scale", "multiple_choice"):
        for o in options:
            choices.append((o.value, o.label))

        if display == "true_false":
            form.true_false.choices = choices

        elif display == "likert_scale":
            #choices = [(c[0], Markup(str(c[1])+"<br/>"+str(c[0]))) for c in choices]
            choices = [(c[0], c[1]) for c in choices]
            form.likert_scale.choices = choices

        elif display == "multiple_choice":
            form.multiple_choice.choices = choices

    elif display == "scale_number":
        args = {}
        for o in Option.query.filter(Option.question == question):
            args[o.label] = o.value

        form.scale_number.render_kw = args

    return form


def create_monitoring(id, form):
    cron_lookup = {'1_1': '0 0 * * *', # once per day
                   '2_1': '0 */12 * * *', # twice per day
                   '1_2': '0 0 * * 1', # once per week
                   '2_2': '0 0 * * 1,5', # twice per week
                   '1_3': '0 0 1 * *', # once per month
                   '2_3': '0 0 */15 * *'} # twice per month

    f = str(form.interval_frequency.data)
    m = str(form.interval_mode.data)
    key = '_'.join([f, m])

    timer = cron_lookup[key]
    cmd = "python test.py"
    arg = str(id)

    cmd_full = ' '.join([cmd, arg])

    cron = CronTab(user='yagci')
    job = cron.new(command=cmd_full)
    job.setall(timer)
    cron.write()
