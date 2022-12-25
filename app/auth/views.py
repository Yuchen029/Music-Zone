from flask import render_template, redirect, request, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from google.auth.jwt import decode as google_jwt_encode

from . import auth
from .. import db
from ..models import User, generate_password_hash
from ..email_sender import send_email
from .forms import LoginForm, RegisterForm, ResetPasswordForm, ResetPasswordApplicationForm


#     PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm


# Detect whether user is authenticated and confirmed.
# If not, direct the user to pertinent page to confirm.
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # search for user in database according to email
        user = User.query.filter_by(email=form.email.data).first()
        # check whether the email and password match each other
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember.data)
            next_route = request.args.get('next')
            if next_route is None or not next_route.startswith('/'):
                if user.role_id == 1:  # staff panel
                    next_route = url_for('admin.index')
                if user.role_id == 2:  # customer panel
                    next_route = url_for('main.index')
            return redirect(next_route)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/login2', methods=['GET', 'POST'])
def login2():
    # LOGIN WITH GOOGLE
    # IMPORTANT !!!! NO TOKEN VALIDATION YET
    user_id_token = request.values.get("token")
    user_data = google_jwt_encode(user_id_token, verify=False)
    """
    sub: user single identification ID
    """
    strong_username = "{}-{}".format(user_data['name'], user_data['sub'])
    user = User.query.filter_by(username=strong_username).first()
    if user is None:
        user = User(
            username=strong_username,
            email=user_data["email"],
            role_id=2,
            password=generate_password_hash("none"),
            avatar_path=user_data['picture'],
            confirmed=True,
            is_google=True
        )
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return jsonify({'status': 0})


# function for registering a new account within the website
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    role_id=2)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
        login_user(user)
        flash('A confirmation email has been sent to your email account.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


# function for logging out the user from the website
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out successfully.')
    return redirect(url_for('main.index'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    # the user has been confirmed before
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    # the user confirms successfully
    if current_user.confirm(token):
        db.session.commit()
        flash('You have accomplished your account confirmation. Enjoy this site!')
    # error
    else:
        flash('The confirmation link is not valid currently.')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('Another confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


# function for user to apply for resetting password
@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordApplicationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
            flash('An email with explanation to reset your password has been sent to you')
        else:
            flash('This email has not been registered before')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_application.html', form=form)


@auth.route('/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been successfully updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password_execution.html', form=form)
