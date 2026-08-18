import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app, session, abort
from flask_login import login_required, current_user
from app.utils.extensions import db
from app.models import LoanType, LoanApplication, FAQ, Notification, ContactMessage, InterestRate, Document
from app.utils.forms import LoanApplicationForm, ContactForm
from app.services import send_async_email, generate_calculator_pdf, generate_receipt_pdf, NotificationService
from decimal import Decimal

main_bp = Blueprint('main', __name__)

def save_document(file_field, doc_type, user_id, application_id=None):
    if not file_field:
        return None
    from app.utils.validators import validate_file_security

    is_secure, res = validate_file_security(
        file_field,
        current_app.config['ALLOWED_EXTENSIONS'],
        current_app.config['MAX_CONTENT_LENGTH']
    )
    if not is_secure:
        return None

    ext = res.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    # Save file size
    file_field.seek(0, os.SEEK_END)
    size = file_field.tell()
    file_field.seek(0)

    file_field.save(filepath)

    # Get mime type
    mime_type = file_field.content_type or 'application/octet-stream'

    doc = Document(
        user_id=user_id,
        loan_application_id=application_id,
        doc_type=doc_type,
        filename=unique_filename,
        original_filename=res,
        file_size=size,
        mime_type=mime_type
    )
    db.session.add(doc)
    db.session.commit()
    return unique_filename

@main_bp.app_context_processor
def inject_notifications():
    if current_user.is_authenticated:
        unread_count = NotificationService.get_unread_count(current_user.id)
        recent_notifs = NotificationService.get_recent(current_user.id, 5)
        return dict(unread_notifs_count=unread_count, recent_notifications=recent_notifs)
    return dict(unread_notifs_count=0, recent_notifications=[])

@main_bp.route('/')
def index():
    loans = LoanType.query.limit(4).all()
    faqs = FAQ.query.limit(5).all()
    partners = ["Global Finance", "Apex Trust", "SecureCap Mutual", "Capital One", "Prime Equity"]
    stats = {
        'customers': '1.2M',
        'disbursed': '$4.5B',
        'branches': '450+',
        'rating': '4.9/5'
    }
    return render_template('index.html', loans=loans, faqs=faqs, partners=partners, stats=stats)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/loans')
def loans():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    min_amount = request.args.get('min_amount', '')
    max_rate = request.args.get('max_rate', '')

    query = LoanType.query
    if search:
        query = query.filter(LoanType.name.like(f"%{search}%") | LoanType.description.like(f"%{search}%"))
    if category:
        query = query.filter(LoanType.category == category)
    if min_amount:
        try:
            amt = Decimal(min_amount)
            query = query.filter(LoanType.max_amount >= amt)
        except Exception:  # nosec B110
            pass
    if max_rate:
        try:
            rate = Decimal(max_rate)
            query = query.filter(LoanType.min_interest_rate <= rate)
        except Exception:  # nosec B110
            pass

    all_loans = query.all()
    categories = db.session.query(LoanType.category).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('loans/loans.html', loans=all_loans, categories=categories, search=search, category=category, min_amount=min_amount, max_rate=max_rate)

@main_bp.route('/loans/<slug>')
def loan_detail(slug):
    loan = LoanType.query.filter_by(slug=slug).first_or_404()
    similar_loans = LoanType.query.filter(LoanType.category == loan.category, LoanType.id != loan.id).limit(3).all()
    return render_template('loans/loan_detail.html', loan=loan, similar_loans=similar_loans)

@main_bp.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        data = request.get_json()
        try:
            amount = Decimal(str(data.get('amount', 0)))
            rate = Decimal(str(data.get('rate', 0)))
            tenure_months = int(data.get('tenure_months', 0))

            from app.services import EMIService
            result = EMIService.calculate_emi(amount, rate, tenure_months)
            schedule = EMIService.generate_amortization_schedule(amount, rate, tenure_months)

            formatted_schedule = []
            for item in schedule:
                formatted_schedule.append({
                    'month': item['month'],
                    'emi': float(item['emi']),
                    'principal': float(item['principal_paid']),
                    'interest': float(item['interest_paid']),
                    'balance': float(item['balance_remaining'])
                })

            return jsonify({
                'emi': float(result['monthly_emi']),
                'total_interest': float(result['total_interest']),
                'total_payment': float(result['total_payable']),
                'schedule': formatted_schedule
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return render_template('calculator/calculator.html')

@main_bp.route('/calculator/pdf', methods=['POST'])
def calculator_pdf():
    try:
        amount = float(request.form.get('amount', 0))
        rate_annual = float(request.form.get('rate', 0))
        tenure = int(request.form.get('tenure', 0))

        if amount <= 0 or rate_annual <= 0 or tenure <= 0:
            flash("Invalid input values for PDF generation.", "warning")
            return redirect(url_for('main.calculator'))

        pdf_buffer = generate_calculator_pdf(amount, rate_annual, tenure)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"LoanSphere_EMI_Schedule_{int(amount)}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        flash(f"Error compiling PDF: {str(e)}", "danger")
        return redirect(url_for('main.calculator'))

@main_bp.route('/eligibility', methods=['GET', 'POST'])
def eligibility():
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        data = request.get_json()
        try:
            age = int(data.get('age', 0))
            income = Decimal(str(data.get('income', 0)))
            credit_score = int(data.get('credit_score', 0))
            existing_emi = Decimal(str(data.get('existing_emi', 0)))

            if age < 21 or age > 65:
                return jsonify({
                    'eligible': False,
                    'reason': 'Age must be between 21 and 65 years.'
                })

            from app.services import EligibilityService
            assessment = EligibilityService.assess_general_limit(income, credit_score, existing_emi)

            if not assessment['eligible']:
                return jsonify({
                    'eligible': False,
                    'reason': assessment['reason']
                })

            max_loan_amount = assessment['max_loan_amount']
            max_allowed_emi = assessment['max_emi']
            rate_annual = assessment['interest_rate_offered']

            recommended_loans = []
            matching_loans = LoanType.query.filter(LoanType.min_amount <= max_loan_amount).all()
            for loan in matching_loans:
                recommended_loans.append({
                    'id': loan.id,
                    'name': loan.name,
                    'slug': loan.slug,
                    'min_rate': float(loan.min_interest_rate),
                    'approval_time': loan.approval_time
                })

            return jsonify({
                'eligible': True,
                'max_loan_amount': float(round(max_loan_amount, 2)),
                'max_emi': float(round(max_allowed_emi, 2)),
                'interest_rate_offered': float(rate_annual),
                'recommended_loans': recommended_loans[:3]
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return render_template('eligibility/eligibility.html')

@main_bp.route('/compare', methods=['GET'])
def compare():
    loan_ids = request.args.getlist('id', type=int)
    all_loans = LoanType.query.all()
    selected_loans = []

    if loan_ids:
        selected_loans = LoanType.query.filter(LoanType.id.in_(loan_ids)).all()

    return render_template('loans/compare.html', all_loans=all_loans, selected_loans=selected_loans)

@main_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    form = LoanApplicationForm()
    loan_types = LoanType.query.all()
    form.loan_type.choices = [(lt.id, lt.name) for lt in loan_types]

    if request.method == 'GET':
        form.full_name.data = current_user.name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.address.data = current_user.address

    if form.validate_on_submit():
        pan_filename = save_document(form.pan_doc.data, 'PAN', current_user.id)
        aadhar_filename = save_document(form.aadhar_doc.data, 'Aadhar', current_user.id)
        salary_filename = save_document(form.salary_slip_doc.data, 'Salary Slip', current_user.id)
        bank_filename = save_document(form.bank_statement_doc.data, 'Bank Statement', current_user.id)

        if not (pan_filename and aadhar_filename and salary_filename and bank_filename):
            flash('Error uploading documents. Please check file sizes and formats.', 'danger')
            return render_template('loans/apply.html', form=form)

        application = LoanApplication(
            user_id=current_user.id,
            loan_type_id=form.loan_type.data,
            full_name=form.full_name.data,
            dob=form.dob.data,
            gender=form.gender.data,
            email=form.email.data.lower(),
            phone=form.phone.data,
            address=form.address.data,
            occupation=form.occupation.data,
            employer=form.employer.data,
            monthly_income=form.monthly_income.data,
            loan_amount=form.loan_amount.data,
            tenure_months=form.tenure_months.data,
            pan_number=form.pan_number.data,
            aadhar_number=form.aadhar_number.data,
            pan_doc=pan_filename,
            aadhar_doc=aadhar_filename,
            salary_slip_doc=salary_filename,
            bank_statement_doc=bank_filename,
            status='Pending'
        )

        db.session.add(application)
        db.session.commit()

        # Link uploaded documents to the new application record
        docs = Document.query.filter_by(user_id=current_user.id, loan_application_id=None).all()
        for doc in docs:
            if doc.filename in [pan_filename, aadhar_filename, salary_filename, bank_filename]:
                doc.loan_application_id = application.id
        db.session.commit()

        NotificationService.notify(
            current_user.id,
            f"Your application for {application.loan_type.name} of INR {application.loan_amount:,.2f} has been submitted successfully (Application ID: {application.id})."
        )

        email_body = f"Hello {application.full_name},\n\nWe have received your loan application for {application.loan_type.name} of amount INR {application.loan_amount:,.2f}.\n\nYour Application Reference ID is {application.id}.\nOur credit officers will review your documents and update your status in 1-2 working days.\n\nYou can track the progress of your application on your LoanSphere Dashboard.\n\nWarm regards,\nLoanSphere Loan Department"
        send_async_email("Loan Application Received - ID " + str(application.id), application.email, email_body)

        flash('Congratulations! Your Loan Application has been submitted successfully.', 'success')
        return redirect(url_for('main.my_applications'))

    return render_template('loans/apply.html', form=form)

@main_bp.route('/my-applications')
@login_required
def my_applications():
    apps = LoanApplication.query.filter_by(user_id=current_user.id).order_by(LoanApplication.applied_at.desc()).all()
    return render_template('loans/my_applications.html', applications=apps)

@main_bp.route('/receipt/<int:app_id>')
@login_required
def download_receipt(app_id):
    app = LoanApplication.query.get_or_404(app_id)
    if app.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    pdf_buffer = generate_receipt_pdf(app)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"LoanSphere_Receipt_ID_{app.id}.pdf",
        mimetype="application/pdf"
    )

@main_bp.route('/loans/document/<filename>')
@login_required
def download_document(filename):
    # Enforce data isolation: verify user ownership or admin privileges
    doc = Document.query.filter_by(filename=filename).first_or_404()
    if doc.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype=doc.mime_type)
    else:
        abort(404)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    apps = LoanApplication.query.filter_by(user_id=current_user.id).order_by(LoanApplication.applied_at.desc()).all()
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()

    total_loans = len(apps)
    pending_loans = sum(1 for a in apps if a.status == 'Pending')
    approved_loans = sum(1 for a in apps if a.status == 'Approved')

    ai_recommendation = None
    if apps:
        latest_applied = apps[0].loan_type.category
        ai_recommendation = LoanType.query.filter(LoanType.category != latest_applied).first()
    else:
        ai_recommendation = LoanType.query.filter_by(slug='personal-loan').first()

    active_approved_apps = [a for a in apps if a.status == 'Approved']

    favorites = session.get('favorite_loans', [])
    fav_loans = LoanType.query.filter(LoanType.id.in_(favorites)).all()

    return render_template('dashboard/dashboard.html',
                           applications=apps,
                           unread_notifs=unread_notifs,
                           total_loans=total_loans,
                           pending_loans=pending_loans,
                           approved_loans=approved_loans,
                           ai_rec=ai_recommendation,
                           approved_apps=active_approved_apps,
                           fav_loans=fav_loans)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=form.name.data,
            email=form.email.data.lower(),
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(msg)
        db.session.commit()
        flash('Thank you for contacting us! We will get back to you shortly.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', form=form)

@main_bp.route('/faqs')
def faqs():
    faq_list = FAQ.query.all()
    search = request.args.get('search', '')
    if search:
        faq_list = FAQ.query.filter(FAQ.question.like(f"%{search}%") | FAQ.answer.like(f"%{search}%")).all()
    return render_template('faqs.html', faqs=faq_list, search=search)

@main_bp.route('/rates')
def rates():
    all_rates = InterestRate.query.filter_by(status='Active').all()
    loan_types = LoanType.query.all()
    return render_template('rates.html', rates=all_rates, loans=loan_types)

@main_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    from app.services import NotificationService
    success = NotificationService.mark_as_read(notif_id, current_user.id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Unauthorized or not found'}), 403

@main_bp.route('/favorites/toggle/<int:loan_id>', methods=['POST'])
@login_required
def toggle_favorite(loan_id):
    favorites = session.get('favorite_loans', [])
    if loan_id in favorites:
        favorites.remove(loan_id)
        action = 'removed'
    else:
        favorites.append(loan_id)
        action = 'added'
    session['favorite_loans'] = favorites
    session.modified = True
    return jsonify({'success': True, 'action': action})

@main_bp.route('/health')
def health():
    try:
        from app.models import LoanType
        LoanType.query.limit(1).all()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception:
        return jsonify({'status': 'unhealthy', 'reason': 'database connection failed'}), 500
