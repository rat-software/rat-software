from .. import app, db
from ..forms import MonitoringForm, ConfirmationForm
from ..models import Monitoring, Country, Query, ResultType, Serp
from ..helpers import create_monitoring
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_security import login_required, current_user
from datetime import datetime
import pandas as pd
from crontab import CronTab

#bp = Blueprint('monitoring', __name__)

@app.route('/monitorings')
@login_required
def monitorings():
    """
    Displays a list of all monitorings.

    Returns:
        Renders the monitorings page with a list of all monitorings.
    """
    monitorings = Monitoring.query.all()
    return render_template('monitorings/monitorings.html', monitorings=monitorings)


@app.route('/monitoring/<id>')
@login_required
def monitoring(id):
    """
    Displays details for a specific monitoring instance.

    Args:
        id (int): The ID of the monitoring to display.

    Returns:
        Renders the monitoring details page with the monitoring's schedule and SERP screenshots.
    """
    m = Monitoring.query.get_or_404(id)

    # Map interval mode and frequency to human-readable strings
    mode = {1: 'day', 2: 'week', 3: 'month'}
    interval_mode = mode[m.interval_mode]

    freq = {1: 'once', 2: 'twice'}
    interval_frequency = freq[m.interval_frequency]

    # Get task schedule from cron
    cron = CronTab(user=True)
    cmd = 'bash /root/monitoring/run_monitoring.sh ' + str(m.id)
    iter = cron.find_command(cmd)
    next = []
    for job in iter:
        schedule = job.schedule(date_from=datetime.now())
        for i in range(0, 5):
            next.append(schedule.get_next())

    # Get SERP screenshots associated with the monitoring
    serp = Serp.query.filter(Serp.monitoring == m)

    return render_template('monitorings/monitoring.html',
                           m=m, next=next, serp=serp,
                           interval_mode=interval_mode,
                           interval_frequency=interval_frequency)


@app.route('/monitoring/new', methods=['GET', 'POST'])
@login_required
def new_monitoring():
    """
    Handles the creation of a new monitoring instance.

    Returns:
        Renders the form for creating a new monitoring or redirects to the monitoring details page if successful.
    """
    form = MonitoringForm()

    # Populate countries choices in the form
    form.countries.choices = [(str(s.id), s.name) for s in Country.query.all()]

    if form.is_submitted():

        # Save queries from form
        queries_ = []
        for query in form.queries.data.splitlines():
            q = Query()
            q.query = query
            q.limit = form.result_count.data if form.result_count.data else 10
            q.created_at = datetime.now()
            queries_.append(q)

        # Get selected result type and countries from the form
        type_ = ResultType.query.get_or_404(form.result_type.data)
        countries_ = [Country.query.get_or_404(id) for id in form.countries.data]

        # Create and configure the new monitoring
        m = Monitoring()
        m.name = form.name.data
        m.description = form.description.data
        m.interval_mode = form.interval_mode.data
        m.interval_frequency = form.interval_frequency.data
        m.created_at = datetime.now()
        m.result_count = form.result_count.data
        m.result_type = type_
        m.queries.extend(queries_)
        m.countries.extend(countries_)

        db.session.commit()

        # Create a new cron job for the monitoring
        cron = CronTab(user=True)
        cmd = 'cd monitoring; python run_monitoring.py ' + str(m.id)
        job = cron.new(command=cmd)

        # Map interval mode and frequency to cron timing
        cron_lookup = {'1_1': '0 0 * * *',  # once per day
                       '2_1': '0 */12 * * *', # twice per day
                       '1_2': '0 0 * * 1', # once per week
                       '2_2': '0 0 * * 1,5', # twice per week
                       '1_3': '0 0 1 * *', # once per month
                       '2_3': '0 0 */15 * *'} # twice per month

        frequency = str(form.interval_frequency.data)
        mode = str(form.interval_mode.data)
        key = '_'.join([frequency, mode])
        timer = cron_lookup[key]
        job.setall(timer)

        cron.write()

        flash('Your monitoring has been created.', 'info')
        return redirect(url_for('monitoring', id=m.id))

    return render_template('monitorings/new_monitoring.html',
                           form=form)


@app.route('/monitoring/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_monitoring(id):
    """
    Deletes a specific monitoring instance.

    Args:
        id (int): The ID of the monitoring to delete.

    Returns:
        Renders the confirmation form for deleting the monitoring or redirects to the dashboard if successful.
    """
    monitoring = Monitoring.query.get_or_404(id)
    form = ConfirmationForm()

    if form.is_submitted():
        if form.cancel.data:
            flash('Monitoring not deleted', 'info')
            return redirect(url_for('monitoring', id=monitoring.id))
        if form.submit.data:
            # Delete associated queries
            for q in monitoring.queries:
                db.session.delete(q)

            # Clear associated countries and delete the monitoring
            monitoring.countries = []
            db.session.delete(monitoring)
            db.session.commit()

            # Remove associated cron job
            cron = CronTab(user=True)
            cmd = 'cd monitoring; python run_monitoring.py ' + str(monitoring.id)
            cron.remove_all(command=cmd)
            cron.write()

            flash('Monitoring deleted', 'success')
            return redirect(url_for('dashboard'))

    return render_template('monitorings/delete_monitoring.html',
                           form=form,
                           monitoring=monitoring)
