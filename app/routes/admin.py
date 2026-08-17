import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import current_user
from app.utils.extensions import db
from app.models import User, LoanType, LoanApplication, EMIHistory, InterestRate, ContactMessage
from app.utils.forms import InterestRateForm
from app.services import send_async_email, NotificationService, LoanService
from decimal import Decimal
from app.utils import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    users_count = User.query.filter_by(is_admin=False).count()
    apps_count = LoanApplication.query.count()
    approved_count = LoanApplication.query.filter_by(status='Approved').count()
    pending_count = LoanApplication.query.filter_by(status='Pending').count()
    total_disbursed = db.session.query(db.func.sum(LoanApplication.loan_amount)).filter_by(status='Approved').scalar() or Decimal('0.00')
    recent_apps = LoanApplication.query.order_by(LoanApplication.applied_at.desc()).limit(10).all()
    unread_messages = ContactMessage.query.filter_by(is_read=False).count()

    return render_template('admin/dashboard.html',
                           users_count=users_count,
                           apps_count=apps_count,
                           approved_count=approved_count,
                           pending_count=pending_count,
                           total_disbursed=total_disbursed,
                           recent_applications=recent_apps,
                           unread_messages=unread_messages)

@admin_bp.route('/users')
@admin_required
def users():
    search = request.args.get('search', '')
    query = User.query.filter_by(is_admin=False)
    if search:
        query = query.filter(User.name.like(f"%{search}%") | User.email.like(f"%{search}%") | User.phone.like(f"%{search}%"))
    all_users = query.all()
    return render_template('admin/users.html', users=all_users, search=search)

@admin_bp.route('/loans')
@admin_required
def loans():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    loan_type_id = request.args.get('loan_type_id', '', type=int)

    query = LoanApplication.query
    if search:
        query = query.filter(LoanApplication.full_name.like(f"%{search}%") | LoanApplication.email.like(f"%{search}%") | LoanApplication.pan_number.like(f"%{search}%"))
    if status:
        query = query.filter(LoanApplication.status == status)
    if loan_type_id:
        query = query.filter(LoanApplication.loan_type_id == loan_type_id)

    apps = query.order_by(LoanApplication.applied_at.desc()).all()
    loan_types = LoanType.query.all()

    return render_template('admin/loans.html', applications=apps, loan_types=loan_types, search=search, status=status, selected_loan_type=loan_type_id)

@admin_bp.route('/loans/<int:app_id>/review', methods=['GET', 'POST'])
@admin_required
def review_application(app_id):
    app = LoanApplication.query.get_or_404(app_id)
    if request.method == 'POST':
        action = request.form.get('action')
        remarks = request.form.get('remarks', '')

        try:
            if action == 'Approve':
                LoanService.transition_status(app, 'Approved', current_user, remarks)
                msg_text = f"Your loan application (ID: {app.id}) for {app.loan_type.name} has been APPROVED! Our relationship manager will connect shortly."
                email_subj = f"Loan Approved - Application ID {app.id}"
                email_body = f"Dear {app.full_name},\n\nWe are pleased to inform you that your application for {app.loan_type.name} (Amount: INR {app.loan_amount:,.2f}) has been APPROVED.\n\nRemarks: {remarks}\n\nOur team will contact you to finalize agreement execution and disbursement.\n\nWarm regards,\nLoanSphere Approvals Team"

                try:
                    rate_annual = app.loan_type.min_interest_rate
                    if rate_annual == 0:
                        emi = app.loan_amount / app.tenure_months
                    else:
                        r = (rate_annual / 100) / 12
                        n = app.tenure_months
                        power = (1 + r) ** n
                        emi = app.loan_amount * r * power / (power - 1)

                    history = EMIHistory(
                        user_id=app.user_id,
                        loan_application_id=app.id,
                        amount_paid=emi,
                        principal_paid=emi * Decimal('0.7'),
                        interest_paid=emi * Decimal('0.3'),
                        balance_remaining=app.loan_amount - (emi * Decimal('0.7')),
                        status='Paid',
                        payment_date=datetime.utcnow() - timedelta(days=15)
                    )
                    db.session.add(history)
                except Exception as e:
                    print(f"Failed to generate mock EMI history: {e}")

            elif action == 'Reject':
                LoanService.transition_status(app, 'Rejected', current_user, remarks)
                msg_text = f"Your loan application (ID: {app.id}) for {app.loan_type.name} was rejected. Details have been emailed."
                email_subj = f"Loan Application Status - Application ID {app.id}"
                email_body = f"Dear {app.full_name},\n\nThank you for your interest in LoanSphere Bank. We regret to inform you that your application for {app.loan_type.name} (Amount: INR {app.loan_amount:,.2f}) was not approved based on our credit guidelines.\n\nReason/Remarks: {remarks}\n\nIf you have any questions, feel free to contact us.\n\nWarm regards,\nLoanSphere Credit Operations"
            else:
                flash('Invalid review action.', 'danger')
                return redirect(url_for('admin.review_application', app_id=app.id))

            db.session.commit()

            NotificationService.notify(app.user_id, msg_text)
            send_async_email(email_subj, app.email, email_body)

            flash(f'Application ID {app.id} successfully {app.status}.', 'success')
            return redirect(url_for('admin.loans'))

        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), 'danger')
            return redirect(url_for('admin.review_application', app_id=app.id))

    return render_template('admin/application_detail.html', app=app)

@admin_bp.route('/loans/document/<filename>')
@admin_required
def view_document(filename):
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    else:
        flash("Document not found or access restricted.", "danger")
        return redirect(url_for('admin.loans'))

@admin_bp.route('/rates', methods=['GET', 'POST'])
@admin_required
def rates():
    form = InterestRateForm()
    loan_types = LoanType.query.all()
    form.loan_type_id.choices = [(lt.id, lt.name) for lt in loan_types]

    if form.validate_on_submit():
        rate = InterestRate(
            loan_type_id=form.loan_type_id.data,
            tenure_months=form.tenure_months.data,
            rate_pct=form.rate_pct.data,
            status=form.status.data,
            effective_from=datetime.utcnow().date()
        )
        db.session.add(rate)
        db.session.commit()
        flash('Interest Rate added successfully!', 'success')
        return redirect(url_for('admin.rates'))

    all_rates = InterestRate.query.all()
    return render_template('admin/rates.html', form=form, rates=all_rates)

@admin_bp.route('/rates/<int:rate_id>/toggle', methods=['POST'])
@admin_required
def toggle_rate(rate_id):
    rate = InterestRate.query.get_or_404(rate_id)
    rate.status = 'Inactive' if rate.status == 'Active' else 'Active'
    db.session.commit()
    return jsonify({'success': True, 'new_status': rate.status})

@admin_bp.route('/messages')
@admin_required
def messages():
    msgs = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    return render_template('admin/messages.html', messages=msgs)

@admin_bp.route('/messages/<int:msg_id>/read', methods=['POST'])
@admin_required
def mark_message_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/analytics')
@admin_required
def analytics():
    status_counts = db.session.query(
        LoanApplication.status, db.func.count(LoanApplication.id)
    ).group_by(LoanApplication.status).all()

    category_disbursements = db.session.query(
        LoanType.name, db.func.sum(LoanApplication.loan_amount)
    ).join(LoanApplication, LoanType.id == LoanApplication.loan_type_id)\
     .filter(LoanApplication.status == 'Approved')\
     .group_by(LoanType.name).all()

    labels_status = [sc[0] for sc in status_counts]
    values_status = [sc[1] for sc in status_counts]

    labels_cat = [cd[0] for cd in category_disbursements]
    values_cat = [float(cd[1]) if cd[1] else 0.0 for cd in category_disbursements]

    return jsonify({
        'status_labels': labels_status,
        'status_values': values_status,
        'category_labels': labels_cat,
        'category_values': values_cat
    })
