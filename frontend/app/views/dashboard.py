
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

        msg = Message(
            subject='RAT Form Submission %s' % (form.name.data),
            sender=form.email.data,
            body=form.message.data,
            recipients=["rat@searchstudies.org"],
        )        

        mail.send(msg)

        flash("Thank you, we have received your message and will get back to you soon.", 'success')
        return redirect('home')



    return render_template('contact.html', form=form, nav=nav)

@app.route('/login_redirect/')
def login_redirect():
    user = User.query.get(current_user.id)  
    user_id = user.id
    logout_user()        

    sql = text('update "user" set active = false where id = :id_user')
    db.session.execute(sql, {'id_user':str(user_id)})
    db.session.commit()

    sql = text('select * from "user" where id = :id_user')
    user_info = db.session.execute(sql, {'id_user':str(user_id)})
    db.session.commit()
    for u in user_info:
        user_mail = u.email

    msg = Message(
        subject='Registration confirmation for RAT',
        sender='rat@searchstudies.org',
        body='Hello %s, \r\n\r\n thank you for your interest in using the RAT.\r\n\r\nWe will contact you in the coming days to discuss your requirements and then activate your account.\r\n\r\nBest,\r\nThe Search Studies Team\r\nhttps://searchstudies.org/' % (user_mail),
        recipients=[user_mail],
    )        

    mail.send(msg)        

    flash("Thank you for registering. We will contact you in the next few days.", 'success')        


    return redirect('/login')


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
