import json
import atexit
import datetime


from flask_login import login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint, redirect, request, flash, url_for, render_template, g

from app import db
from .models import Customers, Games, GameImages, Roles, Comments
from .common_functions import convert_image_from_binary_to_unicode, admin_permission, return_genres, add_to_db


admin_sites = Blueprint("admin", __name__)


@admin_sites.route('/add-game', methods=["GET", "POST"])
@login_required
def add_new_game():
    g.photo = convert_image_from_binary_to_unicode(Customers.query.get(current_user.get_id()).customer_photo)
    if admin_permission() == 2:
        return redirect('/')
    if request.method == 'POST':
        game_name = request.form.get('new_game_name')
        try:
            if float(request.form.get('new_game_price')):
                if float(request.form.get('new_game_price')) < 1000:
                    game_price = float(request.form.get('new_game_price'))
                else:
                    game_price = 999.99
        except ValueError:
            flash('Game price must be numeric!')
            return redirect('')
        game_genre = request.form.getlist('new_game_genre')
        game_description = request.form.get('new_game_description')
        game_image = request.files['new_game_ico'].read()
        new_game = Games(game_name=game_name,
                                game_description=game_description,
                                price=game_price)
        for genre in return_genres():
            if genre.game_type_name in game_genre:
                new_game.genres.append(genre)
        add_to_db(new_game)
        if not game_image:
            with open('app/static/images/mark_edited2.png', 'rb') as default_photo:
                game_image = default_photo.read()
        new_game_image = GameImages(game_id=new_game.game_id, game_photo=game_image)
        add_to_db(new_game_image)
        return redirect(url_for('customer_sites.display_all_games'))
    return render_template('add_game.html', user_photo=g.photo, genres=return_genres())


@admin_sites.route('/<int:game_id>/edit', methods=["GET", "POST"])
def edit_game(game_id: int):
    g.photo = convert_image_from_binary_to_unicode(Customers.query.get(current_user.get_id()).customer_photo)
    if admin_permission() == 2:
        return redirect(f'/{game_id}')
    else:
        game = Games.query.get(game_id)
        game_image = GameImages.query.filter_by(game_id=game_id).first()
        if request.method == "POST":
            game.game_name = request.form.get('new_game_name')
            try:
                if float(request.form.get('new_game_price')):
                    if float(request.form.get('new_game_price')) < 1000:
                        game.price = float(request.form.get('new_game_price'))
                    else:
                        game.price = 999.99
            except ValueError:
                flash('Game price must be numeric!')
                return redirect('')
            game_genres = request.form.getlist('new_game_genre')
            game.game_description = request.form.get('new_game_description')
            game_new_image = request.files['new_game_ico'].read()
            if game_genres:
                game.genres.clear()
                for genre in return_genres():
                    if genre.game_type_name in game_genres:
                        game.genres.append(genre)
            if game_new_image:
                game_image.game_photo = game_new_image
            db.session.commit()
            return redirect("/add-game")
        return render_template('add_game.html',
                               game=game,
                               game_image=game_image,
                               user_photo=g.photo,
                               cart_item_count=g.cart,
                               genres=return_genres())


@admin_sites.route('/hide_game', methods=["POST"])
@login_required
def hide_game():
    game_id = request.json
    game = Games.query.get(game_id)
    if game.is_active:
        game.is_active = False
        game.hidden_timestamp = datetime.datetime.now()
    else:
        game.is_active = True
        game.hidden_timestamp = None
    db.session.commit()
    return 'Ok'


@admin_sites.route('/change_role', methods=["POST"])
@login_required
def ajax_change_role():
    role_id = request.json.get('roleId')
    customer_id = request.json.get('customerId')
    if admin_permission() == 1:
        user = Customers.query.get(customer_id)
        role_name = Roles.query.get(role_id).name
        user.role_id = role_id
        db.session.commit()
        return json.dumps(role_name)


@admin_sites.route('/all_customers')
@login_required
def display_customers():
    g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
    if admin_permission() == 1:
        customers = Customers.query.order_by(Customers.customer_id).all()
        roles = Roles.query.all()
        return render_template('users_list.html', customers=customers, roles=roles, cart_item_count=g.cart, user_photo=g.photo)
    return redirect('/')


@admin_sites.route('/edit_games_quantity')
@login_required
def edit_games_quantity():
    g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
    if admin_permission() == 1:
        games = Games.query.order_by(Games.game_id).all()
        return render_template('games_list.html', games=games, cart_item_count=g.cart, user_photo=g.photo)
    return redirect('/')


@admin_sites.route('/ajax_edit_quantity', methods=["POST"])
def ajax_edit_quantity():
    game_id = request.json.get('gameId')
    new_quantity = request.json.get('newQuantity')
    if admin_permission() == 1:
        try:
            if int(new_quantity):
                game = Games.query.get(game_id)
                game.quantity_available = new_quantity
                db.session.commit()
                return str(game.quantity_available)
        except ValueError:
            return redirect(url_for('admin.edit_games_quantity'))


def check_hidden_games():
    for game in Games.query.all():
        if game.hidden_timestamp is not None \
                and (datetime.datetime.utcnow()-game.hidden_timestamp) > datetime.timedelta(days=90):
            for comment in Comments.query.filter_by(game_id=game.game_id).all():
                db.session.delete(comment)
            db.session.commit()
            db.session.delete(GameImages.query.filter_by(game_id=game.game_id).first())
            db.session.delete(game)
            db.session.commit()


def check_hidden_comments():
    for comment in Comments.query.all():
        if comment.hidden is not None and ((datetime.datetime.utcnow()-comment.hidden) > datetime.timedelta(minutes=5)):
            db.session.delete(comment)
            db.session.commit()


delete_hidden_games = BackgroundScheduler(daemon=True)
delete_hidden_comments = BackgroundScheduler(daemon=True)
delete_hidden_games.add_job(check_hidden_games, 'interval', minutes=60*24*7)
delete_hidden_comments.add_job(check_hidden_comments, 'interval', minutes=1)
delete_hidden_games.start()
delete_hidden_comments.start()
atexit.register(lambda: delete_hidden_games.shutdown())
atexit.register(lambda: delete_hidden_comments.shutdown())
