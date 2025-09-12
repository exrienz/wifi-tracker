from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, db
from .forms import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.environments'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_approved and not user.is_admin:
                flash('Your account is pending approval from an administrator.', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.environments'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.environments'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if this is the first user (becomes admin)
        is_first_user = User.query.count() == 0
        
        user = User(
            username=form.username.data,
            is_admin=is_first_user,
            is_approved=is_first_user
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            if is_first_user:
                flash('Registration successful! You have been granted administrator privileges as the first user.', 'success')
                login_user(user, remember=True)
                return redirect(url_for('main.environments'))
            else:
                flash('Registration successful! Please wait for administrator approval before logging in.', 'info')
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))