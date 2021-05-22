import base64

from flask_login import current_user
from flask import redirect, session, g

from app import db, app
from models import GameGenres, Customers, Cart, CartItem


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
