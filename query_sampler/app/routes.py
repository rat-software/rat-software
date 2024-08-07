# Routes / Views file to define the routes and functions

from flask import Flask, render_template, request, redirect, url_for, send_file 
from app import app
from flask_simplelogin import is_logged_in

from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField 
from wtforms import DecimalField, RadioField, SelectField, TextAreaField, FileField 
from wtforms.validators import InputRequired 

import subprocess
import os
import time
import pandas as pd

# Import custom libraries
from app.forms import *
from app.db import *

# Index page
@app.route('/')
@app.route('/index')
def index():
    """
    Render the index page. If the user is logged in, fetch and display all studies.
    Otherwise, redirect the user to the login page.
    """
    if is_logged_in():  # Check if a user is logged in
        studies = get_studies()  # Retrieve all studies from the database
        return render_template('index.html', title='Home', studies=studies)  # Render the template with the studies
    else:
        return redirect('login')

# Page with legal information
@app.route('/legal')
def legal():
    """
    Render the legal information page.
    """
    return render_template('legal.html', title='Legal Notice')

# Create a new study
@app.route('/create_study', methods=['GET', 'POST'])
def create_study():
    """
    Handle the creation of a new study. If the form is submitted, insert the study into
    the database and redirect to the study's overview page. Otherwise, render the form for creating a study.
    """
    if is_logged_in():
        form = StudyForm()  # Initialize the StudyForm from forms.py

        if form.is_submitted():  # Check if the form has been submitted
            name = form.name.data  # Retrieve the study name from the form
            study_id = insert_study(name)  # Insert the study into the database
            study_id = study_id[0]  # Get the ID of the newly created study
            redirect_url = '/studies/show_study/' + str(study_id)  # Create a URL to redirect to the new study's page
            return redirect(redirect_url)
        else:
            # Render the form for creating a new study
            return render_template('studies/create_study.html', title='Create Study', form=form)
    else:
        return redirect('login')

# Dashboard for a created study
@app.route('/studies/show_study/<id>', methods=['GET', 'POST'])
def show_study(id):
    """
    Display the dashboard for a specific study. If the form for adding keywords is submitted,
    save the keywords and reload the page. Otherwise, render the study details.
    """
    if is_logged_in():
        # Retrieve study details from the database
        study = get_study(id)
        keywords = get_keywords(id)
        keyword_ideas = get_keyword_ideas(id)
        keyword_ideas_count = len(keyword_ideas)  # Count the number of keyword ideas

        status = get_keyword_status_study(id)  # Get the status of keyword operations for the study
        
        # Initialize the KeywordsForm from forms.py
        form = KeywordsForm() 
        regions = get_regions()
        languages = get_languages()     
        # Set choices for form fields based on regions and languages
        form.language_criterion.choices = [(l['criterion_id'], l['name']) for l in languages]
        form.region_criterion.choices = [(r['criterion_id'], r['name']) for r in regions]

        if form.is_submitted():
            # Process and save new keywords
            keywords = form.data['keywords']
            keywords = keywords.split('\n')  # Split keywords by newline
            language = form.data['language_criterion']
            region = form.data['region_criterion']
                        
            for k in keywords:
                k = k.replace('\r', '')  # Remove carriage return characters
                if not check_keyword(id, region, language, k):
                    insert_keyword(id, region, language, k)

            redirect_url = '/studies/show_study/' + str(id)
            return redirect(redirect_url)
        else:
            # Render the study dashboard with current details
            return render_template('studies/show_study.html', title='Study', study=study, keywords=keywords, keyword_ideas_count=keyword_ideas_count, keyword_ideas=keyword_ideas, form=form, status=status)
    else:
        return redirect('login')

# TODO: Form to edit a study
@app.route('/studies/edit_study/<id>', methods=['GET', 'POST'])
def edit_study(id):
    """
    Placeholder for editing a study. Currently returns the study ID.
    """
    if is_logged_in():
        return id
    else:
        return redirect('login')

# TODO: Form to delete a study with all keywords and keyword ideas
@app.route('/studies/delete_study/<id>', methods=['GET', 'POST'])
def delete_study(id):
    """
    Placeholder for deleting a study. Currently returns the study ID.
    """
    if is_logged_in():
        return id
    else:
        return redirect('login')

# Read all keywords from the database to show them on the study dashboard
@app.route('/keywords/<id>', methods=['GET', 'POST'])
def keywords(id):
    """
    Display all keywords associated with a specific study.
    """
    if is_logged_in():
        keywords = get_input_keywords(id)        
        return render_template('keywords/keywords.html', title='Keywords', keywords=keywords)
    else:
        return redirect('login')

# Start /google_ads/generate_keywords.py script to generate the keyword ideas
@app.route('/start_query_sampler/<id>', methods=['GET', 'POST'])
def start_query_sampler(id):
    """
    Start a background process to generate keyword ideas by running an external script.
    Redirect to the study's page after starting the script.
    """
    if is_logged_in():       
        current_directory = os.getcwd()
        script = current_directory + "/google_ads/generate_keywords.py"
        time.sleep(5)  # Pause to avoid immediate redirect issues
        # Start the script in the background
        subprocess.Popen(["python", script, id])
        redirect_url = '/studies/show_study/' + str(id)
        return redirect(redirect_url)
    else:
        return redirect('login')

# Export keyword ideas by using pandas
@app.route('/export_keyword_ideas/<id>', methods=['GET', 'POST'])
def export_keyword_ideas(id):
    """
    Export keyword ideas to a CSV file and provide it for download.
    """
    if is_logged_in():
        current_directory = os.getcwd()
        keyword_ideas = select_keywords_ideas(id)
        path = current_directory + str(id) + "_keyword_ideas.csv"
        filename = str(id) + "_keyword_ideas.csv"
        keyword_ideas.to_csv(path, index=False, encoding='utf-8-sig')

        # Send the CSV file as an attachment for download
        return send_file(path, as_attachment=True, download_name=filename)
    else:
        return redirect('login')
