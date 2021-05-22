from threading import Thread

from flask_mail import Message
from flask_login import current_user
from flask import Blueprint, session, request, flash, redirect, render_template, g

from app import db, mail
from models import Cart, Games, CartItem, Orders, GameImages
from views import add_to_db, convert_image_from_binary_to_unicode, admin_permission


cart_and_order = Blueprint('cart_and_order', __name__)


def is_cart_active():
    user_cart = Cart.query.filter_by(customer_id=current_user.customer_id).order_by(Cart.date.desc()).first()
    try:
        if user_cart.cart_status:
            return True
        return False
    except AttributeError:
        return False


def send_mail(*args, **kwargs):
    msg = Message(f'Order for {args[1]} {args[2]} from game store', recipients=[args[0]])
    with open('static/images/thank_u.png', 'rb') as photo_for_email:
        thank_you_image = photo_for_email.read()
    msg.html = render_template('email.html',
                           thank_you_image=convert_image_from_binary_to_unicode(thank_you_image),
                           customer_first_name=args[1],
                           customer_last_name=args[2],
                           customer_phone=args[3],
                           total_price=sum(map(lambda price: price[0]*price[1], kwargs.get('order_list'))),
                           cart_items=kwargs.get('order_list'))
    mail.send(msg)


@cart_and_order.route('/order', methods=["POST", "GET"])
def order():
    if admin_permission() == 2:
        if request.method == "POST":
            if not current_user.is_authenticated and ('cart' not in session or not len(session['cart'])):
                flash('You have no products added in your Shopping Cart', 'danger')
                return redirect('/order' + '?showAlertOrder=' + 'true')
            else:
                order_first_name = request.form.get("order_first_name")
                order_last_name = request.form.get("order_last_name")
                order_email = request.form.get("order_email")
                order_phone = request.form.get("order_phone")
                payment_type = request.form.get("payment_type")
                comment = request.form.get("comment")
                if not current_user.is_authenticated:
                    if 'cart' in session and len(session['cart']):
                        for index, game in enumerate(session['cart_game_id']):
                            game = Games.query.get(game)
                            game.quantity_available -= session['cart'][index][1]
                        db.session.commit()
                        t = Thread(target=send_mail, args=(order_email, order_first_name, order_last_name, order_phone),
                                             kwargs={'order_list': session['cart']})
                        t.run()
                        session.pop('cart', None)
                        session.pop('cart_game_id', None)
                        flash('Thank you, we will send the game licenses to the email you wrote in the order form',
                              'success')
                        return redirect('/order' + '?showAlertOrder=' + 'true')
                elif current_user.is_authenticated:
                    user_cart = Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                        Cart.date.desc()).first()
                    user_cart.cart_status = False
                    user_cart_items = CartItem.query.filter_by(cart_id=user_cart.cart_id).all()
                    order_list = []
                    for elem in user_cart_items:
                        game = Games.query.get(elem.game_id)
                        game.quantity_available -= elem.amount
                        order_list.append((float(game.price), elem.amount, game.game_name))
                    if Orders.query.filter_by(cart_id=user_cart.cart_id).first():
                        flash('You have no products added in your Shopping Cart', 'danger')
                        return redirect('/order' + '?showAlertOrder=' + 'true')
                    new_order = Orders(cart_id=user_cart.cart_id,
                                              customer_first_name=order_first_name,
                                              customer_last_name=order_last_name,
                                              customer_email=order_email,
                                              customer_phone=order_phone,
                                              payment_type=payment_type,
                                              comment=comment)
                    add_to_db(new_order)
                    t = Thread(target=send_mail, args=(order_email, order_first_name, order_last_name, order_phone),
                               kwargs={'order_list': order_list})
                    t.run()
                    flash('Thank you, we will send the game licenses to the email you wrote in the order form',
                          'success')
                    return redirect('/order' + '?showAlertOrder=' + 'true')
        return render_template('order.html', user_photo=g.photo, cart_item_count=g.cart)
    return redirect('/')


@cart_and_order.route('/cart', methods=["POST", "GET"])
def cart():
    if not current_user.is_authenticated:
        if 'cart' in session:
            cart_items = session['cart']
            game_details = [Games.query.get(item) for item in session['cart_game_id']]
            cart_items_images = [convert_image_from_binary_to_unicode(
                GameImages.query.filter_by(game_id=elem).first().game_photo) for elem in session['cart_game_id']]
        else:
            return render_template('cart.html', user_photo=g.photo, cart_item_count=g.cart)
    elif current_user.is_authenticated:
        if admin_permission() == 1:
            return redirect('/')
        else:
            user_cart = Cart.query.filter_by(customer_id=current_user.customer_id).order_by(Cart.date.desc()).first()
            if user_cart.cart_status:
                cart_items = CartItem.query.filter_by(cart_id=user_cart.cart_id).order_by(CartItem.cart_item_id).all()
                cart_items_images = [convert_image_from_binary_to_unicode(
                    GameImages.query.filter_by(game_id=elem.game_id).first().game_photo) for elem in cart_items]
                game_details = [Games.query.get(item.game_id) for item in cart_items]
            else:
                return render_template('cart.html', user_photo=g.photo, cart_item_count=g.cart)
    return render_template('cart.html',
                           cart_items=cart_items,
                           cart_items_images=cart_items_images,
                           game_details=game_details,
                           cart_item_count=g.cart,
                           user_photo=g.photo)


@cart_and_order.route('/ajax_add_to_cart', methods=["POST"])
def ajax_add_to_cart():
    if request.method == "POST":
        game = Games.query.get(int(request.json))
        if not current_user.is_authenticated:
            if request.json not in session['cart_game_id']:
                session['cart'].append([float(game.price), 1, game.game_name])
                session['cart_game_id'].append(request.json)
            else:
                cart_id = session['cart_game_id'].index(request.json)
                session['cart'][cart_id][1] += 1
        else:
            if current_user.role_id == 2:
                if is_cart_active():
                    user_cart = Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                        Cart.date.desc()).first()
                    cart_items = CartItem.query.filter_by(cart_id=user_cart.cart_id).all()
                    cart_items_id = [item.game_id for item in cart_items]
                    if request.json in cart_items_id:
                        game_index = cart_items_id.index(request.json)
                        cart_items[game_index].amount += 1
                        cart_items[game_index].price = cart_items[game_index].amount * game.price
                        db.session.commit()
                    else:
                        new_cart_item = CartItem(game_id=request.json, price=game.price, cart_id=user_cart.cart_id)
                        add_to_db(new_cart_item)
                        cart_items.append(new_cart_item)
                elif not is_cart_active():
                    user_cart = Cart(customer_id=current_user.customer_id)
                    add_to_db(user_cart)
                    new_cart_item = CartItem(game_id=int(request.json), price=game.price, cart_id=user_cart.cart_id)
                    add_to_db(new_cart_item)
    return str(len(session['cart'])) if not current_user.is_authenticated \
        else str(len(CartItem.query.filter_by(cart_id=user_cart.cart_id).all()))


@cart_and_order.route('/ajax_delete_from_cart', methods=["POST"])
def ajax_delete_from_cart():
    if request.method == "POST":
        game = Games.query.get(int(request.json))
        if not current_user.is_authenticated:
            cart_id = session['cart_game_id'].index(request.json)
            if session['cart'][cart_id][1] > 1:
                session['cart'][cart_id][1] -= 1
        elif current_user.is_authenticated:
            if admin_permission() == 2:
                user_cart = Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                    Cart.date.desc()).first()
                if user_cart.cart_status:
                    cart_items = CartItem.query.filter_by(cart_id=user_cart.cart_id).all()
                    cart_items_id = [item.game_id for item in cart_items]
                    game_index = cart_items_id.index(request.json)
                    if cart_items[game_index].amount > 1:
                        cart_items[game_index].amount -= 1
                        cart_items[game_index].price = cart_items[game_index].amount * game.price
                        db.session.commit()
    return str(len(session['cart'])) if not current_user.is_authenticated \
        else str(len(CartItem.query.filter_by(cart_id=user_cart.cart_id).all()))


@cart_and_order.route('/ajax_delete_cart_item', methods=["POST"])
def ajax_delete_cart_item():
    if request.method == "POST":
        if not current_user.is_authenticated:
            cart_id = session['cart_game_id'].index(request.json)
            session['cart'].pop(cart_id)
            session['cart_game_id'].pop(cart_id)
        elif current_user.is_authenticated:
            user_cart = Cart.query.filter_by(customer_id=current_user.customer_id).order_by(Cart.date.desc()).first()
            cart_item = CartItem.query.get(request.json)
            db.session.delete(cart_item)
            db.session.commit()
    return str(len(session['cart'])) if not current_user.is_authenticated \
        else str(len(CartItem.query.filter_by(cart_id=user_cart.cart_id).all()))
