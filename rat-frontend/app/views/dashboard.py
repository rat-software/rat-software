"""
Dashboard module for the RAT application.

This module controls central account views, dashboard components for individual 
and administrative study listings, contact form submission handling via automated mailer 
protocols, and intermediate user intercept views like forced password reset rules.
It also includes Super Admin analytics endpoints for tracking application usage.
"""

from .. import app, db, mail
from app.models import User, Role, Qs_Study, Study, AnalyticsEvent
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
from sqlalchemy import func, or_, and_, exists, distinct
from sqlalchemy.orm import aliased

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

SUPER_ADMIN_ROLE_NAME = 'Super Admin'


def get_super_admin_ids():
    """
    Returns the IDs of all team accounts (super_admin flag OR 'Super Admin' role).
    Their activity is reported separately so that internal RAT usage does not
    inflate the regular usage metrics.
    Note: this uses the CURRENT super admin status, so recalculated history
    (export / full sync) is attributed according to today's roles.
    """
    rows = db.session.query(User.id).filter(
        or_(
            User.super_admin.is_(True),
            User.roles.any(Role.name == SUPER_ADMIN_ROLE_NAME)
        )
    ).all()
    return [r[0] for r in rows]


def _study_is_super_admin(study_users_rel, super_ids):
    """
    A study counts as a 'Super Admin' study if it is linked to at least one super admin
    and to NO regular user. Everything else (incl. mixed teams) counts as 'Regular Users'.
    """
    return and_(
        study_users_rel.any(User.id.in_(super_ids)),
        ~study_users_rel.any(User.id.notin_(super_ids))
    )


def get_newsletter_subscribers():
    """
    Returns newsletter subscribers in registration order, NEWEST FIRST.

    Sorting uses the user ID (serial, assigned at sign-up) instead of a date column:
    create_datetime was not stored for registrations for a long time, and the fallback
    dates (confirmed_at / last_login_at) are NOT the sign-up date (last_login_at even
    changes with every login). The ID always reflects the real sign-up order, including
    users who have not confirmed their email yet.
    """
    return User.query.filter(User.newsletter_opt_in.is_(True)).order_by(User.id.desc()).all()


def build_newsletter_rows(unknown_label='Unknown (email not confirmed)'):
    """
    Builds the [Email, Registered At] rows for the newsletter list (newest first).
    Date = stored registration date; for older accounts without one, the email
    confirmation date (usually the day of sign-up) is used.
    """
    rows = []
    for u in get_newsletter_subscribers():
        best_date = u.create_datetime or u.confirmed_at
        rows.append([u.email, best_date.strftime('%Y-%m-%d') if best_date else unknown_label])
    return rows


def get_daily_analytics(target_date, super_ids=None):
    """
    Calculates statistics for a SINGLE specific day (00:00:00 to 23:59:59).
    This creates the "Daily Row" format perfect for marketing and Data Studio.

    User-related metrics are split into "Regular Users" and "Super Admins" (team accounts).
    'super_ids' can be passed in by callers that loop over many days to avoid re-querying.
    """
    if super_ids is None:
        super_ids = get_super_admin_ids()

    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    start_of_month = datetime(target_date.year, target_date.month, 1)

    # Safely fallback to confirmed_at or last_login_at if create_datetime is NULL
    user_date = func.coalesce(User.create_datetime, User.confirmed_at, User.last_login_at)

    # 1. Base counts for this day (Tägliche Deltas)
    new_users = User.query.filter(user_date >= start_of_day, user_date < end_of_day).count()

    # 2. Studies created this day, split by Regular Users / Super Admins
    rat_super = _study_is_super_admin(Study.users, super_ids)
    qs_super = _study_is_super_admin(Qs_Study.users, super_ids)

    def count_studies(model, super_pred, *conditions):
        base = model.query.filter(model.created_at >= start_of_day, model.created_at < end_of_day, *conditions)
        sa = base.filter(super_pred).count()
        return base.count() - sa, sa  # (regular, super admin)

    rat_reg, rat_sa = count_studies(Study, rat_super)
    qs_reg, qs_sa = count_studies(Qs_Study, qs_super)
    human_reg, human_sa = count_studies(Study, rat_super, or_(
        Study.study_mode.in_(['human', 'hybrid']),
        Study.answers.any()  # Fallback: Studie hat echte Antworten von Probanden
    ))
    survey_reg, survey_sa = count_studies(Study, rat_super, Study.pre_survey_json != None)
    clf_reg, clf_sa = count_studies(Study, rat_super, or_(
        Study.classifier.any(),
        Study.classifier_results.any(),     # Fallback: Hat klassische Classifier-Ergebnisse
        Study.classifier_indicators.any()   # Fallback: Hat LLM-Indikator-Ergebnisse
    ))

    # 3. Events for this day (Tägliche Deltas), split by the acting user.
    #    Events of deleted users (user_id NULL) count as regular usage.
    def count_event(e_type):
        base = AnalyticsEvent.query.filter(
            AnalyticsEvent.event_type == e_type,
            AnalyticsEvent.timestamp >= start_of_day,
            AnalyticsEvent.timestamp < end_of_day
        )
        sa = base.filter(AnalyticsEvent.user_id.in_(super_ids)).count()
        return base.count() - sa, sa

    downloads_reg, downloads_sa = count_event('extension_download')
    uploads_reg, uploads_sa = count_event('data_upload')
    exports_reg, exports_sa = count_event('study_export')
    logins_reg, logins_sa = count_event('login')

    # Participants are anonymous -> attribute them via the study they joined
    super_study_ids = db.session.query(Study.id).filter(rat_super)
    parts_base = AnalyticsEvent.query.filter(
        AnalyticsEvent.event_type == 'participant_joined',
        AnalyticsEvent.timestamp >= start_of_day,
        AnalyticsEvent.timestamp < end_of_day
    )
    parts_sa = parts_base.filter(AnalyticsEvent.study_id.in_(super_study_ids)).count()
    parts_reg = parts_base.count() - parts_sa

    # 4. Unique Users (monthly basis):
    #    A user is counted on the day of their FIRST login within the calendar month.
    #    Further logins of the same user in that month are not counted again.
    #    -> Summing this column per month = individual users who logged in that month.
    earlier = aliased(AnalyticsEvent)
    first_login_of_month = AnalyticsEvent.query.filter(
        AnalyticsEvent.event_type == 'login',
        AnalyticsEvent.user_id.isnot(None),
        AnalyticsEvent.timestamp >= start_of_day,
        AnalyticsEvent.timestamp < end_of_day,
        ~exists().where(and_(
            earlier.event_type == 'login',
            earlier.user_id == AnalyticsEvent.user_id,
            earlier.timestamp >= start_of_month,
            earlier.timestamp < start_of_day
        ))
    )

    def count_unique(*conditions):
        return first_login_of_month.filter(*conditions).with_entities(
            func.count(distinct(AnalyticsEvent.user_id))
        ).scalar() or 0

    unique_sa = count_unique(AnalyticsEvent.user_id.in_(super_ids))
    unique_reg = count_unique(AnalyticsEvent.user_id.notin_(super_ids))

    # 5. Newsletter metrics (Daily Opt-ins only)
    new_newsletter = User.query.filter(
        user_date >= start_of_day,
        user_date < end_of_day,
        User.newsletter_opt_in.is_(True)
    ).count()

    # IMPORTANT: The first 13 columns keep their ORIGINAL names and order, because the
    # Google Sheet is used directly as a data source (Looker Studio). They now contain
    # REGULAR USERS ONLY (super admins excluded). New columns are only appended at the end.
    return {
        "Date": target_date.strftime('%Y-%m-%d'),
        "New Registrations": new_users,
        "Logins": logins_reg,
        "RAT Studies Created": rat_reg,
        "QS Studies Created": qs_reg,
        "New Human Assessment Studies": human_reg,
        "New Studies w/ Surveys": survey_reg,
        "New Studies w/ Classifiers": clf_reg,
        "Participants Joined": parts_reg,
        "Extension Downloads": downloads_reg,
        "Data Uploads": uploads_reg,
        "Results Exported": exports_reg,
        "New Newsletter Opt-Ins": new_newsletter,
        # --- appended columns ---
        # Unique Users: user counted on the day of their first login in the calendar month
        # (sum per month = individual users of that month)
        "Unique Users": unique_reg,
        "Unique Users (Super Admins)": unique_sa,
        "Logins (Super Admins)": logins_sa,
        "RAT Studies Created (Super Admins)": rat_sa,
        "QS Studies Created (Super Admins)": qs_sa,
        "New Human Assessment Studies (Super Admins)": human_sa,
        "New Studies w/ Surveys (Super Admins)": survey_sa,
        "New Studies w/ Classifiers (Super Admins)": clf_sa,
        "Participants Joined (Super Admins)": parts_sa,
        "Extension Downloads (Super Admins)": downloads_sa,
        "Data Uploads (Super Admins)": uploads_sa,
        "Results Exported (Super Admins)": exports_sa,
    }


def get_monthly_unique_users(start_date, end_date, super_ids=None):
    """
    One row per calendar month (YYYY-MM) between start_date and end_date with the
    number of individual users who logged in at least once in that month.
    Login events are only tracked since the AnalyticsEvent table exists, so earlier months show 0.
    """
    if super_ids is None:
        super_ids = get_super_admin_ids()

    rows = []
    month = date(start_date.year, start_date.month, 1)
    while month <= end_date:
        next_month = date(month.year + (month.month // 12), month.month % 12 + 1, 1)
        base = db.session.query(func.count(distinct(AnalyticsEvent.user_id))).filter(
            AnalyticsEvent.event_type == 'login',
            AnalyticsEvent.user_id.isnot(None),
            AnalyticsEvent.timestamp >= datetime.combine(month, datetime.min.time()),
            AnalyticsEvent.timestamp < datetime.combine(min(next_month, end_date + timedelta(days=1)), datetime.min.time())
        )
        rows.append({
            "Month": month.strftime('%Y-%m'),
            "Unique Users": base.filter(AnalyticsEvent.user_id.notin_(super_ids)).scalar() or 0,
            "Unique Users (Super Admins)": base.filter(AnalyticsEvent.user_id.in_(super_ids)).scalar() or 0,
        })
        month = next_month
    return rows


# ==============================================================================
# COLUMN DEFINITIONS (written to the "Column Definitions" tab)
# Keep in sync with the keys of get_daily_analytics() - a test checks this.
# ==============================================================================

_REGULAR_NOTE = " Nur normale Nutzer (Super Admins herausgerechnet, siehe Spalte mit Zusatz '(Super Admins)')."
_STUDY_NOTE = (" Eine Studie zählt als Super-Admin-Studie, wenn ihr ausschließlich Super Admins zugeordnet sind;"
               " gemischte Studien zählen als normale Nutzung. Gelöschte Studien sind nicht enthalten.")

DAILY_COLUMN_DEFINITIONS = {
    "Date": "Kalendertag (Serverzeit, UTC), 00:00 bis 24:00 Uhr. Alle Werte einer Zeile sind Tageswerte (keine kumulierten Summen).",
    "New Registrations": "Anzahl der an diesem Tag registrierten Nutzerkonten (alle Konten inkl. Super Admins). Ältere Konten ohne gespeichertes Registrierungsdatum werden über das Datum der E-Mail-Bestätigung zugeordnet.",
    "Logins": "Anzahl der Logins an diesem Tag. Jeder Login zählt, auch mehrere desselben Nutzers." + _REGULAR_NOTE,
    "RAT Studies Created": "Anzahl der an diesem Tag angelegten RAT-Studien." + _REGULAR_NOTE + _STUDY_NOTE,
    "QS Studies Created": "Anzahl der an diesem Tag angelegten Query-Sampler-Studien (QS)." + _REGULAR_NOTE + _STUDY_NOTE,
    "New Human Assessment Studies": "Teilmenge von 'RAT Studies Created': Studien im Modus 'human' oder 'hybrid' bzw. Studien, für die bereits Bewertungen von Teilnehmenden vorliegen. Maßgeblich ist der Stand zum Zeitpunkt der Berechnung." + _REGULAR_NOTE,
    "New Studies w/ Surveys": "Teilmenge von 'RAT Studies Created': Studien mit hinterlegtem Fragebogen vor der Studie (Pre-Survey). Maßgeblich ist der Stand zum Zeitpunkt der Berechnung." + _REGULAR_NOTE,
    "New Studies w/ Classifiers": "Teilmenge von 'RAT Studies Created': Studien mit mindestens einem zugewiesenen Classifier oder vorhandenen Classifier-/LLM-Indikator-Ergebnissen. Maßgeblich ist der Stand zum Zeitpunkt der Berechnung." + _REGULAR_NOTE,
    "Participants Joined": "Anzahl der Teilnehmenden, die an diesem Tag einer Studie beigetreten sind. Teilnehmende sind anonym und werden über die Studie zugeordnet (Studie normaler Nutzer vs. Super-Admin-Studie).",
    "Extension Downloads": "Anzahl der Downloads der RAT-Browser-Extension." + _REGULAR_NOTE,
    "Data Uploads": "Anzahl erfolgreich importierter Daten-Uploads (CSV) in eine Studie." + _REGULAR_NOTE,
    "Results Exported": "Anzahl der Excel-Exporte von Studienergebnissen." + _REGULAR_NOTE,
    "New Newsletter Opt-Ins": "Anzahl der an diesem Tag registrierten Konten, die bei der Registrierung den Newsletter abonniert haben (alle Konten).",
    "Unique Users": ("Individuelle Nutzer: Jeder Nutzer wird nur am Tag seines ERSTEN Logins im Kalendermonat gezählt; weitere Logins im selben Monat zählen nicht erneut. "
                     "Die Summe über einen Monat ergibt die Zahl der Nutzer, die sich in diesem Monat mind. einmal eingeloggt haben. "
                     "Nicht über mehrere Monate summieren (dort würden Nutzer mehrfach gezählt) - dafür den Reiter 'Monthly Unique Users' nutzen." + _REGULAR_NOTE),
}

SUPER_ADMIN_DEFINITION_SUFFIX = (
    "Wie '{base}', aber nur für Super Admins (Team-Accounts mit Super-Admin-Flag oder Rolle 'Super Admin'). "
    "Maßgeblich ist der heutige Super-Admin-Status, auch für zurückliegende Tage."
)

OTHER_SHEET_DEFINITIONS = [
    ("Monthly Unique Users", "Month", "Kalendermonat (JJJJ-MM)."),
    ("Monthly Unique Users", "Unique Users", "Anzahl individueller normaler Nutzer, die sich in diesem Monat mind. einmal eingeloggt haben (Super Admins herausgerechnet)."),
    ("Monthly Unique Users", "Unique Users (Super Admins)", "Anzahl individueller Super Admins, die sich in diesem Monat mind. einmal eingeloggt haben."),
    ("Newsletter List", "Email", "E-Mail-Adresse aller Konten mit Newsletter-Opt-in. Sortiert nach Anmeldung, neueste zuerst."),
    ("Newsletter List", "Registered At", "Registrierungsdatum; bei älteren Konten ohne gespeichertes Datum das Datum der E-Mail-Bestätigung. 'Unknown (email not confirmed)' = E-Mail noch nicht bestätigt, kein Datum bekannt."),
]


def build_definition_rows(daily_columns, daily_sheet_name="Daily Time Series"):
    """
    Returns [Sheet, Column, Definition] rows for all columns of all analytics tabs,
    in the same order as they appear in the sheets.
    """
    rows = []
    for col in daily_columns:
        if col.endswith(" (Super Admins)"):
            base = col[:-len(" (Super Admins)")]
            definition = SUPER_ADMIN_DEFINITION_SUFFIX.format(base=base)
        else:
            definition = DAILY_COLUMN_DEFINITIONS.get(col, "")
        rows.append([daily_sheet_name, col, definition])
    rows.extend([list(r) for r in OTHER_SHEET_DEFINITIONS])
    return rows


DEFINITION_HEADER = ["Sheet", "Column", "Definition"]


def get_analytics_start_date():
    """The very first day the app was used (earliest known user date)."""
    first_date = db.session.query(
        func.min(func.coalesce(User.create_datetime, User.confirmed_at, User.last_login_at))
    ).scalar()
    if first_date:
        return first_date.date()
    return (datetime.utcnow() - timedelta(days=30)).date()


def _get_or_create_worksheet(spreadsheet, title, cols):
    try:
        return spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows="1000", cols=str(cols))


def _write_side_sheets(spreadsheet, start_date, end_date, super_ids, daily_columns):
    """Overwrites the 'Newsletter List', 'Monthly Unique Users' and 'Column Definitions' tabs completely."""
    def_sheet = _get_or_create_worksheet(spreadsheet, "Column Definitions", 3)
    def_sheet.clear()
    def_sheet.update(
        values=[DEFINITION_HEADER] + build_definition_rows(daily_columns, spreadsheet.sheet1.title),
        range_name="A1"
    )

    news_sheet = _get_or_create_worksheet(spreadsheet, "Newsletter List", 2)
    news_sheet.clear()
    news_sheet.update(values=[["Email", "Registered At"]] + build_newsletter_rows(), range_name="A1")

    monthly = get_monthly_unique_users(start_date, end_date, super_ids)
    if monthly:
        uu_sheet = _get_or_create_worksheet(spreadsheet, "Monthly Unique Users", 3)
        uu_sheet.clear()
        uu_sheet.update(values=[list(monthly[0].keys())] + [list(r.values()) for r in monthly], range_name="A1")
    
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
    super_ids = get_super_admin_ids()
    stats = get_daily_analytics(yesterday, super_ids)

    target_date = stats['Date']
    row_data = list(stats.values())

    # Guard: never append rows whose columns don't match the sheet header
    # (e.g. after new metrics were added). The full sync rebuilds the sheet.
    header = sheet.row_values(1)
    if header and header != list(stats.keys()):
        raise RuntimeError(
            "Column layout of the Google Sheet differs from the current metrics. "
            "Run 'flask sync-analytics-full' once to rebuild the sheet with the new columns."
        )

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
    # TEIL 2: Newsletter Liste (nach Anmeldedatum sortiert) und
    #         Monthly Unique Users auf eigenen Tabs (Überschreiben)
    # ---------------------------------------------------------
    _write_side_sheets(spreadsheet, get_analytics_start_date(), yesterday, super_ids, list(stats.keys()))

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
    start_date = get_analytics_start_date()
    end_date = (datetime.utcnow() - timedelta(days=1)).date()
    super_ids = get_super_admin_ids()

    # 2. Build the Time Series Data (Day by Day)
    data = []
    delta = end_date - start_date
    for i in range(delta.days + 1):
        target_day = start_date + timedelta(days=i)
        data.append(get_daily_analytics(target_day, super_ids))

    df_stats = pd.DataFrame(data)
    df_unique = pd.DataFrame(get_monthly_unique_users(start_date, end_date, super_ids))

    # 3. Newsletter Email List (sorted by registration date, oldest first)
    df_subs = pd.DataFrame(build_newsletter_rows(), columns=["Email", "Registered At"])

    # 4. Write everything to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_stats.to_excel(writer, sheet_name='Daily Time Series', index=False)

        if not df_unique.empty:
            df_unique.to_excel(writer, sheet_name='Monthly Unique Users', index=False)
            writer.sheets['Monthly Unique Users'].set_column('A:C', 28)

        df_defs = pd.DataFrame(build_definition_rows(list(df_stats.columns)), columns=DEFINITION_HEADER)
        df_defs.to_excel(writer, sheet_name='Column Definitions', index=False)
        def_ws = writer.sheets['Column Definitions']
        wrap = writer.book.add_format({'text_wrap': True, 'valign': 'top'})
        def_ws.set_column('A:A', 22, wrap)
        def_ws.set_column('B:B', 45, wrap)
        def_ws.set_column('C:C', 110, wrap)

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
        start_date = get_analytics_start_date()
        end_date = (datetime.utcnow() - timedelta(days=1)).date()
        super_ids = get_super_admin_ids()

        # 2. Datenmatrix aufbauen (Header kommen direkt aus get_daily_analytics,
        #    damit Spalten und Werte nie auseinanderlaufen)
        data_matrix = []

        delta = end_date - start_date
        total_days = delta.days + 1
        
        print(f"Insgesamt zu berechnende Tage: {total_days} (von {start_date} bis {end_date})")
        print("-" * 50)
        
        for i in range(total_days):
            target_day = start_date + timedelta(days=i)
            # Terminal Output aktualisieren, flush=True pusht es direkt in die Konsole
            print(f"[{i+1}/{total_days}] Berechne Daten für {target_day}... ", end="", flush=True)
            
            stats = get_daily_analytics(target_day, super_ids)
            if not data_matrix:
                data_matrix.append(list(stats.keys()))
            data_matrix.append(list(stats.values()))
            
            print("Erledigt.")
            
        print("-" * 50)
        print("Schreibe Daten in Google Sheets... (Das kann einige Sekunden dauern)")
            
        # 3. Komplettes Sheet leeren und mit allen historischen Daten füllen
        sheet.clear()
        sheet.update(values=data_matrix, range_name="A1")
        
        # 4. Newsletter Liste (sortiert) und Monthly Unique Users aktualisieren
        _write_side_sheets(spreadsheet, start_date, end_date, super_ids, data_matrix[0])

        print(f"✅ ERFOLG! {len(data_matrix)-1} Tage an Historie wurden ins Google Sheet übertragen.")
        
    except Exception as e:
        print(f"\n❌ Fehler beim Full Sync: {str(e)}")