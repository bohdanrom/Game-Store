import base64
import datetime
import atexit

from flask_login import current_user
from flask import redirect, session, g
from apscheduler.schedulers.background import BackgroundScheduler

from app import db, app
from models import GameGenres, Customers, Cart, CartItem, Games, GameImages, Comments


def check_hidden_games():
    for game in Games.query.all():
        if game.hidden_timestamp is not None \
                and (datetime.datetime.now()-game.hidden_timestamp) > datetime.timedelta(days=90):
            for comment in Comments.query.filter_by(game_id=game.game_id).all():
                db.session.delete(comment)
            db.session.commit()
            db.session.delete(GameImages.query.filter_by(game_id=game.game_id).first())
            db.session.delete(game)
            db.session.commit()


delete_hidden_games = BackgroundScheduler(daemon=True)
delete_hidden_games.add_job(check_hidden_games, 'interval', minutes=60*24*7)
delete_hidden_games.start()
atexit.register(lambda: delete_hidden_games.shutdown())


def return_genres():
    genres = GameGenres.query.all()
    return genres


def convert_image_from_binary_to_unicode(image):
    try:
        decoded_image = base64.b64encode(image).decode("utf-8")
    except AttributeError:
        decoded_image = None
    except TypeError:
        decoded_image = None
    return decoded_image


def admin_permission():
    try:
        user_role = Customers.query.get(current_user.get_id()).role_id
    except AttributeError:
        user_role = 2
    return user_role


def add_to_db(row):
    db.session.add(row)
    db.session.commit()


@app.after_request
def redirect_to_login_page(response):
    if response.status_code == 401:
        return redirect('/' + '?showModal=' + 'true')
    return response


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)


@app.before_request
def load_users():
    if current_user.is_authenticated:
        try:
            g.user = current_user.get_id()
            g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
            g.cart_id = Cart.query.filter_by(customer_id=g.user).order_by(
                Cart.date.desc()).first()
            if g.cart_id.cart_status:
                g.cart = len(CartItem.query.filter_by(cart_id=g.cart_id.cart_id).all())
            else:
                g.cart = 0
        except AttributeError:
            g.user = None
            g.photo = None
            g.cart = 0
    else:
        g.user = None
        g.photo = None
        g.cart = len(session['cart']) if 'cart' in session else 0


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
