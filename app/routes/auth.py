import os
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.utils.extensions import db
from app.models import User
from app.utils.forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm, ProfileForm
from app.services import send_async_email, NotificationService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def save_document(file_field):
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
    file_field.save(filepath)
    return unique_filename

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()
        if existing_user:
            flash('An account with this email address already exists.', 'danger')
            return render_template('auth/register.html', form=form)

        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            phone=form.phone.data,
            address=form.address.data,
            verification_token=uuid.uuid4().hex,
            email_verified=False
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        verify_url = url_for('auth.verify_email', token=user.verification_token, _external=True)
        email_body = f"Hello {user.name},\n\nWelcome to LoanSphere Bank! Please click the following link to verify your email address:\n{verify_url}\n\nWarm regards,\nLoanSphere Team"
        send_async_email("Verify your LoanSphere Account", user.email, email_body)

        flash('Registration successful! A verification link has been sent to your email.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.name}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.email_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your email address has been successfully verified! You can now log in.', 'success')
        NotificationService.notify(user.id, "Your email address has been verified. Welcome to LoanSphere!")
    else:
        flash('Invalid or expired email verification link.', 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            user.reset_token = uuid.uuid4().hex
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=2)
            db.session.commit()

            reset_url = url_for('auth.reset_password', token=user.reset_token, _external=True)
            email_body = f"Hello {user.name},\n\nYou requested a password reset for your LoanSphere account. Click the link below to set a new password:\n{reset_url}\n\nNote: This link expires in 2 hours.\n\nIf you did not request this, please ignore this email."
            send_async_email("Reset Password - LoanSphere", user.email, email_body)

        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    user = User.query.filter(User.reset_token == token, User.reset_token_expiry > datetime.utcnow()).first()
    if not user:
        flash('Invalid or expired password reset token.', 'danger')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash('Your password has been successfully reset! You can now log in.', 'success')
        NotificationService.notify(user.id, "Your account password was successfully updated.")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        if form.email.data.lower() != current_user.email:
            existing = User.query.filter_by(email=form.email.data.lower()).first()
            if existing:
                flash('Email is already taken by another account.', 'danger')
                return render_template('profile/profile.html', form=form)
            current_user.email = form.email.data.lower()
            current_user.email_verified = False

        current_user.name = form.name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data

        if form.photo.data:
            photo_file = save_document(form.photo.data)
            if photo_file:
                current_user.photo = photo_file

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        NotificationService.notify(current_user.id, "Your profile details were updated.")
        return redirect(url_for('auth.profile'))

    return render_template('profile/profile.html', form=form)
