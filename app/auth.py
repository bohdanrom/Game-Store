from datetime import timedelta, datetime

from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, request, redirect, url_for, flash, session, g

from .common_functions import add_to_db
from .models import Customers, Roles


auth = Blueprint("auth", __name__)


@auth.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_login = request.form.get('user_email')
        user_password = request.form.get('user_password')
        session['remember'] = datetime.utcnow() if request.form.get('remember') else None
        if user_login and user_password:
            user_credentials = Customers.query.filter_by(customer_email=user_login).first()
            if user_credentials and check_password_hash(user_credentials.customer_password, user_password):
                login_user(user_credentials, duration=timedelta(days=7))
                return redirect(url_for('customer_sites.display_all_games', user_photo=g.photo))
            flash('Incorrect password')
            return redirect('/' + '?showModal=' + 'true')
        flash('Please, fill both fields email and password')
        return redirect('/' + '?showModal=' + 'true')
    return redirect(url_for('customer_sites.display_all_games', user_photo=g.photo, cart_item_count=g.cart))


@auth.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        new_user_first_name = request.form.get('first_name')
        new_user_last_name = request.form.get('last_name')
        new_user_login = request.form.get('email')
        new_user_username = request.form.get('user_name')
        new_user_password = request.form.get('password')
        new_user_password_verification = request.form.get('password_two')
        if not (
                new_user_first_name or new_user_last_name or new_user_login or new_user_password or
                new_user_password_verification):
            flash('Please, fill all the fields')
            return redirect('/' + '?showModalSignUp=' + 'true')
        elif new_user_password != new_user_password_verification:
            flash('Passwords not match')
            return redirect('/' + '?showModalSignUp=' + 'true')
        else:
            if new_user_password_verification == new_user_password:
                if Customers.query.filter_by(customer_email=new_user_login).first():
                    flash('A user with this email already exists')
                    return redirect('/' + '?showModalSignUp=' + 'true')
                elif Customers.query.filter_by(customer_username=new_user_username).first():
                    flash('Someone already has that username')
                    return redirect('/' + '?showModalSignUp=' + 'true')
                else:
                    hash_password = generate_password_hash(new_user_password)
                    new_user = Customers(customer_first_name=new_user_first_name,
                                                customer_last_name=new_user_last_name,
                                                customer_username=new_user_username,
                                                customer_email=new_user_login,
                                                customer_password=hash_password,
                                                role=Roles.query.get(2))
                    add_to_db(new_user)
                    login_user(new_user)
                    return redirect(url_for('customer_sites.display_all_games', user_photo=g.photo, cart_item_count=g.cart))
    return redirect(url_for('customer_sites.display_all_games', user_photo=g.photo, cart_item_count=g.cart))


@auth.route('/logout', methods=["POST", "GET"])
@login_required
def logout():
    session.pop('remember', None)
    logout_user()
    session.pop('cart', None)
    session.pop('cart_game_id', None)
    return redirect(url_for('customer_sites.display_all_games', cart_item_count=g.cart))
