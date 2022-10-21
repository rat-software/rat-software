from .. import app, db
from app.models import User
from ..forms import ContactForm
from flask import render_template, request, redirect, flash
from flask_security import login_required, current_user
from flask_mailman import EmailMessage


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

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    nav = 'static'
    form = ContactForm()

    if form.is_submitted():
        msg = EmailMessage(
            '%s wants to know more about RAT' % (form.name.data),
            form.message.data,
            form.email.data,
            ['info@searchstudies.org', 'nurce.yagci@haw-hamburg.de']
        )

        msg.send()

        flash("Thank you, we have recieved your message and will get back to you soon.", 'success')
        return redirect('home')



    return render_template('contact.html', form=form, nav=nav)


@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(current_user.id)

    return render_template('dashboard.html', user=user)

@app.route('/')
def main():
    if current_user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('home')
