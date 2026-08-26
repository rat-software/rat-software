"""
Dashboard module for the RAT application.

This module controls central account views, dashboard components for individual 
and administrative study listings, contact form submission handling via automated mailer 
protocols, and intermediate user intercept views like forced password reset rules.
"""

from .. import app, db, mail
from app.models import User, Qs_Study, Study
from ..forms import ContactForm
from flask import render_template, redirect, flash, url_for, current_app, request
from flask_security import login_required, current_user
from flask_security.utils import hash_password
from flask_mail import Message
from flask import render_template, redirect, flash, url_for, current_app, request, jsonify

@app.route('/')
def main():
    """
    Root application route providing authentication-based routing.

    Redirects authenticated sessions directly to their main dashboard views 
    while forcing unauthenticated sessions to the secure login gateway page.

    Args:
        None

    Returns:
        Response: A Flask redirect response object.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('security.login'))


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Processes contact form validations and handles automated mail submission routing.

    Flashes status indicators to notify the user of successful deliveries 
    or unexpected SMTP service connectivity dropouts.

    Args:
        None

    Returns:
        str: Rendered contact form view layout or custom dashboard redirect instructions.
    """
    nav = 'static'
    form = ContactForm()
    if form.validate_on_submit():
        try:
            msg = Message(
                subject=f"RAT Form Submission from {form.name.data}",
                sender=current_app.config['SECURITY_EMAIL_SENDER'],
                recipients=["contact@rat-software.org"],
                body=f"Name: {form.name.data}\nEmail: {form.email.data}\n\nMessage:\n{form.message.data}",
                html=f"<strong>Name:</strong> {form.name.data}<br>" \
                     f"<strong>Email:</strong> {form.email.data}<br><br>" \
                     f"<strong>Message:</strong><br>{form.message.data}"
            )
            mail.send(msg)
            flash("Thank you, we have received your message and will get back to you soon.", 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            current_app.logger.error(f"Mail sending failed: {e}")
            flash("An error occurred while sending your message.", 'danger')
            
    return render_template('contact.html', form=form, nav=nav)

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    """
    Handles background AJAX submissions from the floating feedback widget.
    Only allows logged-in users to submit and automatically uses their account email.
    """
    data = request.get_json()
    message_body = data.get('message', '').strip()

    if not message_body:
        return jsonify({'success': False, 'error': 'Message cannot be empty.'}), 400

    try:
        msg = Message(
            subject=f"RAT User Feedback from {current_user.email}",
            sender=current_app.config['SECURITY_EMAIL_SENDER'],
            recipients=["contact@rat-software.org"],
            body=f"User: {current_user.email}\n\nFeedback:\n{message_body}",
            html=f"<strong>User:</strong> {current_user.email}<br><br><strong>Feedback:</strong><br>{message_body.replace(chr(10), '<br>')}"
        )
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Thank you! Your feedback has been sent.'})
        
    except Exception as e:
        current_app.logger.error(f"Feedback mail sending failed: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while sending your message.'}), 500

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """
    Renders the principal tracking dashboard summarizing user-specific and system-wide metrics.

    Intercepts the workflow to demand credential security updates if an account flag 
    mandates a forced password change. Compiles lists of standard RAT studies, 
    query sampler entities, and presents unrestricted database views if an administrative 
    profile token is validated.

    Args:
        None

    Returns:
        str: Rendered dashboard template context matrices or intermediate view overrides.
    """
    user = User.query.get(current_user.id)
    
    # ==============================================================================
    # FORCED PASSWORD RESET VIEW OVERRIDE
    # ==============================================================================
    if getattr(user, 'force_password_change', False):
        if request.method == 'POST':
            password = request.form.get('password')
            password_confirm = request.form.get('password_confirm')
            
            if not password or len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
            elif password != password_confirm:
                flash('The passwords you typed do not match.', 'danger')
            else:
                user.password = hash_password(password)
                user.force_password_change = False
                db.session.commit()
                flash('Your new secure password has been saved! Account activated.', 'success')
                return redirect(url_for('dashboard'))
                
        return render_template('security/reset_password.html', forced_mode=True)    
    # ==============================================================================
    
    # 1. Own RAT Studies
    rat_studies = Study.query.filter(
        Study.users.any(id=user.id),
        Study.visible == True
    ).order_by(Study.created_at.desc()).all()
    
    # 2. Own Query Sampler Studies
    qs_studies = Qs_Study.query.filter(
        Qs_Study.users.any(id=user.id),
        Qs_Study.visible == True
    ).order_by(Qs_Study.created_at.desc()).all()
    
    # 3. Super Admin view
    other_rat_studies = []
    other_qs_studies = []
    
    if getattr(user, 'super_admin', False) == True:
        other_rat_studies = Study.query.filter(Study.visible == True).order_by(Study.created_at.desc()).all()
        other_qs_studies = Qs_Study.query.filter(Qs_Study.visible == True).order_by(Qs_Study.created_at.desc()).all()
    
    return render_template('dashboard.html', 
                           user=user, 
                           rat_studies=rat_studies, 
                           qs_studies=qs_studies,
                           other_rat_studies=other_rat_studies,
                           other_qs_studies=other_qs_studies)


@app.route('/roadmap')
def roadmap():
    """
    Renders the public application development roadmap timeline.

    Args:
        None

    Returns:
        str: Rendered roadmap visualization template layout.
    """
    nav = 'static'
    return render_template('roadmap.html', nav=nav)