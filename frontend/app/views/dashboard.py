from .. import app, db, mail
from app.models import User, Qs_Study, Study
from ..forms import ContactForm
from flask import render_template, request, redirect, flash, url_for, current_app
from flask_security import login_required, current_user
from flask_mail import Message

@app.route('/')
def main():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        # Hier nutzen wir direkt security.login, um den BuildError zu vermeiden
        return redirect(url_for('security.login'))


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
            return redirect(url_for('dashboard'))
        except Exception as e:
            current_app.logger.error(f"Mail sending failed: {e}")
            flash("An error occurred while sending your message.", 'danger')
            
    return render_template('contact.html', form=form, nav=nav)

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(current_user.id)
    
    # 1. RAT Studies: Wir holen alle Studies, wo der User verknüpft ist, 
    # und sortieren direkt in der Datenbank absteigend (neueste zuerst).
    rat_studies = Study.query.filter(
        Study.users.any(id=user.id),
        Study.visible == True
    ).order_by(Study.created_at.desc()).all()
    
    
    # 2. Query Sampler Studies: Das Gleiche für QS Studies.
    qs_studies = Qs_Study.query.filter(
        Qs_Study.users.any(id=user.id),
        Qs_Study.visible == True
    ).order_by(Qs_Study.created_at.desc()).all()
    
    return render_template('dashboard.html', 
                           user=user, 
                           rat_studies=rat_studies, 
                           qs_studies=qs_studies)


@app.route('/roadmap')
def roadmap():
    nav = 'static'
    return render_template('roadmap.html', nav=nav)
