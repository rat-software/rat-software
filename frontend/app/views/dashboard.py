from .. import app, db, mail, security
from app.models import User
from ..forms import ContactForm
from flask import render_template, request, redirect, flash
from flask_security import login_required, current_user, logout_user
from flask_mail import Message
from sqlalchemy.sql.expression import func
from sqlalchemy import text
from sqlalchemy import create_engine
import time

@app.route('/home')
def home():
    """
    Renders the home page.

    Returns:
        Rendered HTML template for the home page.
    """
    nav = 'static'
    return render_template('home.html', nav=nav)

@app.route('/features')
def features():
    """
    Renders the features page.

    Returns:
        Rendered HTML template for the features page.
    """
    nav = 'static'
    return render_template('features.html', nav=nav)

@app.route('/tool_selection')
def tool_selection():

    nav = 'static'
    return render_template('tool_selection.html', nav=nav)

@app.route('/about')
def about():
    """
    Renders the about page.

    Returns:
        Rendered HTML template for the about page.
    """
    nav = 'static'
    return render_template('about.html', nav=nav)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Handles contact form submission and sends an email.

    Returns:
        Rendered HTML template for the contact page, or redirects to the home page after form submission.
    """
    nav = 'static'
    form = ContactForm()

    if form.is_submitted():
        # Create a new email message with form data
        msg = Message(
            subject='RAT Form Submission %s' % (form.name.data),
            sender=form.email.data,
            body=form.message.data,
            recipients=["recipent_email"],
        )        

        # Send the email
        mail.send(msg)

        # Flash a success message and redirect to the home page
        flash("Thank you, we have received your message and will get back to you soon.", 'success')
        return redirect('home')

    return render_template('contact.html', form=form, nav=nav)

@app.route('/login_redirect/')
def login_redirect():
    """
    Logs out the current user, marks the user as inactive in the database,
    sends a registration confirmation email, and redirects to the login page.

    Returns:
        Redirect to the login page after processing.
    """
    # Get current user and log out
    user = User.query.get(current_user.id)  
    user_id = user.id
    logout_user()        

    # Update user's status to inactive in the database
    sql = text('update "user" set active = false where id = :id_user')
    db.session.execute(sql, {'id_user': str(user_id)})
    db.session.commit()

    # Retrieve user's email for sending confirmation
    sql = text('select * from "user" where id = :id_user')
    user_info = db.session.execute(sql, {'id_user': str(user_id)})
    db.session.commit()
    for u in user_info:
        user_mail = u.email

    # Create and send a registration confirmation email
    msg = Message(
        subject='Registration confirmation for RAT',
        sender='your_sender',
        body='Hello %s, \r\n\r\n thank you for your interest in using the RAT.\r\n\r\nWe will contact you in the coming days to discuss your requirements and then activate your account.\r\n\r\nBest,\r\nThe Search Studies Team\r\nhttps://searchstudies.org/' % (user_mail),
        recipients=[user_mail],
    )        

    mail.send(msg)        

    # Flash a success message and redirect to the login page
    flash("Thank you for registering. We will contact you in the next few days.", 'success')        
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Renders the dashboard page for logged-in users.

    Returns:
        Rendered HTML template for the dashboard page.
    """
    user = User.query.get(current_user.id)
    return render_template('dashboard.html', user=user)

@app.route('/')
def main():
    """
    Redirects authenticated users to the dashboard and unauthenticated users to the home page.

    Returns:
        Redirects to the dashboard if the user is authenticated; otherwise, redirects to the home page.
    """
    if current_user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('home')
