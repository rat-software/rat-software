from .. import app, db, mail
from app.models import User, Qs_Study
from ..forms import ContactForm
from flask import render_template, request, redirect, flash, url_for, current_app
from flask_security import login_required, current_user
from flask_mail import Message

@app.route('/home')
def home():
    nav = 'static'
    return render_template('home.html', nav=nav)

@app.route('/features')
def features():
    nav = 'static'
    return render_template('features.html', nav=nav)

@app.route('/about')
def about():
    nav = 'static'
    return render_template('about.html', nav=nav)

@app.route('/roadmap')
def roadmap():
    nav = 'static'
    return render_template('roadmap.html', nav=nav)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    nav = 'static'
    form = ContactForm()
    if form.validate_on_submit():
        try:
            # Erstellt eine E-Mail-Nachricht mit Flask-Mail
            msg = Message(
                subject=f"RAT Form Submission from {form.name.data}",
                sender=current_app.config['SECURITY_EMAIL_SENDER'],
                recipients=["sebastian.suenkler@haw-hamburg.de"],
                body=f"Name: {form.name.data}\nEmail: {form.email.data}\n\nMessage:\n{form.message.data}",
                html=f"<strong>Name:</strong> {form.name.data}<br>" \
                     f"<strong>Email:</strong> {form.email.data}<br><br>" \
                     f"<strong>Message:</strong><br>{form.message.data}"
            )
            # Verwendet die zentrale mail-Instanz zum Senden
            mail.send(msg)
            flash("Thank you, we have received your message and will get back to you soon.", 'success')
            return redirect(url_for('home'))
        except Exception as e:
            current_app.logger.error(f"Mail sending failed: {e}")
            flash("An error occurred while sending your message.", 'danger')
            
    return render_template('contact.html', form=form, nav=nav)

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(current_user.id)
    
    # Lade die regulären Studien (wie bisher)
    rat_studies = user.studies
    
    # NEU: Lade die Query Sampler Studien über die neue Relationship
    qs_studies = user.qs_studies
    
    return render_template('dashboard.html', 
                           user=user, 
                           rat_studies=rat_studies, 
                           qs_studies=qs_studies)

@app.route('/')
def main():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('home'))