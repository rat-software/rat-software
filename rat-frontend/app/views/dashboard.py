"""
Dashboard module for the RAT application.

This module controls central account views, dashboard components for individual 
and administrative study listings, contact form submission handling via automated mailer 
protocols, and intermediate user intercept views like forced password reset rules.
It also includes Super Admin analytics endpoints for tracking application usage.
"""

from .. import app, db, mail
from app.models import User, Qs_Study, Study, AnalyticsEvent
from ..forms import ContactForm
from flask import render_template, redirect, flash, url_for, current_app, request, jsonify, make_response
from flask_security import login_required, current_user
from flask_security.utils import hash_password
from flask_login import user_logged_in
from flask_mail import Message

# Analytics & Export imports
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta, date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import func, or_

# ==============================================================================
# EVENT TRACKING SIGNALS
# ==============================================================================

@user_logged_in.connect_via(app)
def track_login(sender, user, **extra):
    """Automatically records a login event every time a user authenticates."""
    db.session.add(AnalyticsEvent(event_type='login', user_id=user.id))
    db.session.commit()

# ==============================================================================
# ANALYTICS HELPER FUNCTIONS (TIME SERIES)
# ==============================================================================

def get_daily_analytics(target_date):
    """
    Calculates statistics for a SINGLE specific day (00:00:00 to 23:59:59).
    This creates the "Daily Row" format perfect for marketing and Data Studio.
    """
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    
    # Safely fallback to confirmed_at or last_login_at if create_datetime is NULL
    user_date = func.coalesce(User.create_datetime, User.confirmed_at, User.last_login_at)
    
    # 1. Base counts for this day (Tägliche Deltas)
    new_users = User.query.filter(user_date >= start_of_day, user_date < end_of_day).count()
    new_rat_studies = Study.query.filter(Study.created_at >= start_of_day, Study.created_at < end_of_day).count()
    new_qs_studies = Qs_Study.query.filter(Qs_Study.created_at >= start_of_day, Qs_Study.created_at < end_of_day).count()
    
    # 2. Study Feature breakdown: TÄGLICHE DELTAS (Gefixt: Start-Datum wieder hinzugefügt!)
    # Dadurch läuft die Abfrage blitzschnell, da nur Studien dieses EINEN Tages geprüft werden.
    human_studies_new = Study.query.filter(
        Study.created_at >= start_of_day,
        Study.created_at < end_of_day,
        or_(
            Study.study_mode.in_(['human', 'hybrid']),
            Study.answers.any()  # Fallback: Studie hat echte Antworten von Probanden
        )
    ).count()
    
    survey_studies_new = Study.query.filter(
        Study.created_at >= start_of_day,
        Study.created_at < end_of_day,
        Study.pre_survey_json != None
    ).count()
    
    clf_studies_new = Study.query.filter(
        Study.created_at >= start_of_day,
        Study.created_at < end_of_day,
        or_(
            Study.classifier.any(),
            Study.classifier_results.any(),     # Fallback: Hat klassische Classifier-Ergebnisse
            Study.classifier_indicators.any()   # Fallback: Hat LLM-Indikator-Ergebnisse
        )
    ).count()

    # 3. Events for this day (Tägliche Deltas)
    def count_event(e_type):
        return AnalyticsEvent.query.filter(
            AnalyticsEvent.event_type == e_type,
            AnalyticsEvent.timestamp >= start_of_day,
            AnalyticsEvent.timestamp < end_of_day
        ).count()

    downloads = count_event('extension_download')
    uploads = count_event('data_upload')
    exports = count_event('study_export')
    logins = count_event('login')
    parts_joined = count_event('participant_joined')
    
    # 4. Newsletter metrics (Daily Opt-ins only)
    new_newsletter = User.query.filter(
        user_date >= start_of_day, 
        user_date < end_of_day,
        User.newsletter_opt_in.is_(True)
    ).count()
    
    return {
        "Date": target_date.strftime('%Y-%m-%d'),
        "New Registrations": new_users,
        "Logins": logins,
        "RAT Studies Created": new_rat_studies,
        "QS Studies Created": new_qs_studies,
        "New Human Assessment Studies": human_studies_new,
        "New Studies w/ Surveys": survey_studies_new,
        "New Studies w/ Classifiers": clf_studies_new,
        "Participants Joined": parts_joined,
        "Extension Downloads": downloads,
        "Data Uploads": uploads,
        "Results Exported": exports,
        "New Newsletter Opt-Ins": new_newsletter
    }
    
@app.route('/')
def main():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('security.login'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
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
    user = User.query.get(current_user.id)
    
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
    
    rat_studies = Study.query.filter(Study.users.any(id=user.id), Study.visible == True).order_by(Study.created_at.desc()).all()
    qs_studies = Qs_Study.query.filter(Qs_Study.users.any(id=user.id), Qs_Study.visible == True).order_by(Qs_Study.created_at.desc()).all()
    
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
    nav = 'static'
    return render_template('roadmap.html', nav=nav)
    
    
# ==============================================================================
# GOOGLE SHEETS CORE LOGIC & CLI COMMAND
# ==============================================================================

def perform_google_sheets_sync():
    """Core logic to push yesterday's data to Google Sheets without duplicates."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('google-service-account.json', scope)
    client = gspread.authorize(creds)
    
    # Öffne das Google Sheet Dokument
    spreadsheet = client.open("RAT Analytics Dashboard")
    
    # ---------------------------------------------------------
    # TEIL 1: Tägliche Statistik (auf dem ersten Tab)
    # ---------------------------------------------------------
    sheet = spreadsheet.sheet1
    
    # Calculate exactly "Yesterday" so it's a complete 24-hour metric
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    stats = get_daily_analytics(yesterday)
    
    target_date = stats['Date']
    row_data = list(stats.values())
    
    # Existing dates from Column A
    existing_dates = sheet.col_values(1)
    
    if target_date in existing_dates:
        row_index = existing_dates.index(target_date) + 1
        sheet.update(values=[row_data], range_name=f"A{row_index}")
        action = "updated"
    else:
        sheet.append_row(row_data)
        action = "added"
        
    # ---------------------------------------------------------
    # TEIL 2: Newsletter Liste auf zweitem Tab (Überschreiben)
    # ---------------------------------------------------------
    try:
        news_sheet = spreadsheet.worksheet("Newsletter List")
    except gspread.exceptions.WorksheetNotFound:
        # Wenn der Tab nicht existiert, wird er automatisch angelegt
        news_sheet = spreadsheet.add_worksheet(title="Newsletter List", rows="1000", cols="2")
        
    subscribers = User.query.filter_by(newsletter_opt_in=True).all()
    news_data = [["Email", "Registered At"]] # Tabellenkopf
    
    for u in subscribers:
        best_date = u.create_datetime or u.confirmed_at or u.last_login_at
        news_data.append([
            u.email,
            best_date.strftime('%Y-%m-%d') if best_date else 'Legacy Admin (Unknown Date)'
        ])
        
    # Alten Inhalt löschen und aktuelle Liste komplett neu reinschreiben
    news_sheet.clear()
    news_sheet.update(values=news_data, range_name="A1")
        
    return target_date, action

@app.cli.command("sync-analytics")
def sync_analytics_cli():
    """
    CLI Command to push yesterday's analytics to Google Sheets.
    Run this via terminal: flask sync-analytics
    """
    try:
        date_synced, action = perform_google_sheets_sync()
        if action == "updated":
            print(f"✅ Successfully UPDATED existing data for {date_synced} in Google Sheets!")
        else:
            print(f"✅ Successfully APPENDED new daily data for {date_synced} to Google Sheets!")
    except Exception as e:
        print(f"❌ Failed to sync with Google Sheets. Error: {str(e)}")   

# ==============================================================================
# SUPER ADMIN ANALYTICS ROUTES
# ==============================================================================

@app.route('/admin/export-statistics')
@login_required
def export_statistics():
    """
    Generates an ALL-TIME daily time-series Excel file.
    Also appends a separate sheet containing Newsletter opt-in email addresses.
    """
    if not getattr(current_user, 'super_admin', False):
        return "Unauthorized", 403

    # 1. Determine the very first day the app was used
    first_user = User.query.order_by(
        func.coalesce(User.create_datetime, User.confirmed_at, User.last_login_at).asc()
    ).filter(
        func.coalesce(User.create_datetime, User.confirmed_at, User.last_login_at).isnot(None)
    ).first()
    
    if first_user:
        start_date = (first_user.create_datetime or first_user.confirmed_at or first_user.last_login_at).date()
    else:
        start_date = (datetime.utcnow() - timedelta(days=30)).date()
        
    end_date = (datetime.utcnow() - timedelta(days=1)).date()
    
    # 2. Build the Time Series Data (Day by Day)
    data = []
    delta = end_date - start_date
    for i in range(delta.days + 1):
        target_day = start_date + timedelta(days=i)
        data.append(get_daily_analytics(target_day))
        
    df_stats = pd.DataFrame(data)
    
    # 3. Generate Newsletter Email List for the second sheet
    subscribers = User.query.filter_by(newsletter_opt_in=True).all()
    
    subscriber_data = []
    for u in subscribers:
        best_date = u.create_datetime or u.confirmed_at or u.last_login_at
        subscriber_data.append({
            "Email": u.email, 
            "Registered At": best_date.strftime('%Y-%m-%d') if best_date else 'Legacy Admin (Unknown Date)'
        })
        
    df_subs = pd.DataFrame(subscriber_data)
    
    # 4. Write both to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_stats.to_excel(writer, sheet_name='Daily Time Series', index=False)
        
        if not df_subs.empty:
            df_subs.to_excel(writer, sheet_name='Newsletter List', index=False)
            worksheet = writer.sheets['Newsletter List']
            worksheet.set_column('A:A', 35) 
            worksheet.set_column('B:B', 25)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=rat_daily_analytics.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

@app.route('/admin/sync-google-sheets', methods=['POST'])
@login_required
def sync_google_sheets():
    """
    Manual fallback route just in case the Super Admin wants to force a sync via the UI.
    """
    if not getattr(current_user, 'super_admin', False):
        return "Unauthorized", 403
        
    try:
        date_synced, action = perform_google_sheets_sync()
        if action == "updated":
            flash(f"Overwrote existing data! Successfully updated {date_synced} in Google Sheets.", 'success')
        else:
            flash(f"Successfully pushed new daily data for {date_synced} to Google Sheets!", 'success')
    except Exception as e:
        current_app.logger.error(f"Google Sheets Sync failed: {e}")
        flash(f'Failed to sync with Google Sheets. Check your service account credentials. Error: {str(e)}', 'danger')
        
    return redirect(url_for('dashboard'))
    
@app.cli.command("sync-analytics-full")
def sync_analytics_full_cli():
    """
    Einmaliger Befehl, um die KOMPLETTE Historie (Tag 1 bis heute) 
    in das Google Sheet zu schreiben. 
    Im Terminal ausführen mit: flask sync-analytics-full
    """
    import sys
    try:
        print("Starte vollständigen historischen Sync. Baue Google Sheets Verbindung auf...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('google-service-account.json', scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open("RAT Analytics Dashboard")
        sheet = spreadsheet.sheet1
        
        # 1. Startdatum finden
        first_user = User.query.order_by(
            func.coalesce(User.create_datetime, User.confirmed_at, User.last_login_at).asc()
        ).filter(
            func.coalesce(User.create_datetime, User.confirmed_at, User.last_login_at).isnot(None)
        ).first()
        
        if first_user:
            start_date = (first_user.create_datetime or first_user.confirmed_at or first_user.last_login_at).date()
        else:
            start_date = (datetime.utcnow() - timedelta(days=30)).date()
            
        end_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        # 2. Datenmatrix aufbauen (Achtung: Spaltennamen wurden auf 'New ...' angepasst!)
        headers = [
            "Date", "New Registrations", "Logins", "RAT Studies Created", "QS Studies Created", 
            "New Human Assessment Studies", "New Studies w/ Surveys", "New Studies w/ Classifiers", 
            "Participants Joined", "Extension Downloads", "Data Uploads", "Results Exported", 
            "New Newsletter Opt-Ins"
        ]
        data_matrix = [headers]
        
        delta = end_date - start_date
        total_days = delta.days + 1
        
        print(f"Insgesamt zu berechnende Tage: {total_days} (von {start_date} bis {end_date})")
        print("-" * 50)
        
        for i in range(total_days):
            target_day = start_date + timedelta(days=i)
            # Terminal Output aktualisieren, flush=True pusht es direkt in die Konsole
            print(f"[{i+1}/{total_days}] Berechne Daten für {target_day}... ", end="", flush=True)
            
            stats = get_daily_analytics(target_day)
            data_matrix.append(list(stats.values()))
            
            print("Erledigt.")
            
        print("-" * 50)
        print("Schreibe Daten in Google Sheets... (Das kann einige Sekunden dauern)")
            
        # 3. Komplettes Sheet leeren und mit allen historischen Daten füllen
        sheet.clear()
        sheet.update(values=data_matrix, range_name="A1")
        
        # 4. Newsletter Liste aktualisieren
        try:
            news_sheet = spreadsheet.worksheet("Newsletter List")
        except gspread.exceptions.WorksheetNotFound:
            news_sheet = spreadsheet.add_worksheet(title="Newsletter List", rows="1000", cols="2")
            
        subscribers = User.query.filter_by(newsletter_opt_in=True).all()
        news_data = [["Email", "Registered At"]]
        for u in subscribers:
            best_date = u.create_datetime or u.confirmed_at or u.last_login_at
            news_data.append([
                u.email,
                best_date.strftime('%Y-%m-%d') if best_date else 'Legacy Admin'
            ])
            
        news_sheet.clear()
        news_sheet.update(values=news_data, range_name="A1")
        
        print(f"✅ ERFOLG! {len(data_matrix)-1} Tage an Historie wurden ins Google Sheet übertragen.")
        
    except Exception as e:
        print(f"\n❌ Fehler beim Full Sync: {str(e)}")