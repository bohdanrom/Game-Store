import base64
from datetime import datetime, timedelta

import humanize
from flask import render_template, request, redirect, flash, url_for, session, g, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db, models, manager


def return_genres():
    genres = models.GameGenres.query.all()
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
        user_role = models.Customers.query.get(current_user.get_id()).role_id
    except AttributeError:
        user_role = 2
    return user_role


def is_cart_active():
    user_cart = models.Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
        models.Cart.date.desc()).first()
    try:
        if user_cart.cart_status:
            return True
        return False
    except AttributeError:
        return False


def add_to_db(row):
    db.session.add(row)
    db.session.commit()


@app.after_request
def redirect_to_login_page(response):
    if response.status_code == 401:
        return redirect('/' + '?showModal=' + 'true')
    return response


@app.route('/add-game', methods=["GET", "POST"])
@login_required
def add_new_game():
    g.photo = convert_image_from_binary_to_unicode(models.Customers.query.get(current_user.get_id()).customer_photo)
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
        new_game = models.Games(game_name=game_name,
                                game_description=game_description,
                                price=game_price)
        for genre in return_genres():
            if genre.game_type_name in game_genre:
                new_game.genres.append(genre)
        add_to_db(new_game)
        if not game_image:
            with open('./static/mark_edited2.png', 'rb') as default_photo:
                game_image = default_photo.read()
        new_game_image = models.GameImages(game_id=new_game.game_id,
                                           game_photo=game_image)
        add_to_db(new_game_image)
        return redirect(url_for('display_all_games'))
    return render_template('add_game.html', user_photo=g.photo, genres=return_genres())


@app.route('/delete_comment', methods=["POST"])
@login_required
def delete_comment():
    comment_id = request.json
    comment = models.Comments.query.get(int(comment_id))
    if comment.author_username == current_user.customer_username or admin_permission() == 1:
        db.session.delete(comment)
        db.session.commit()
    return "Ok"


@app.route('/<int:game_id>', methods=["GET", "POST"])
def display_game(game_id: int):
    game_details = models.Games.query.filter_by(game_id=game_id).first()
    if game_details.is_active:
        if request.method == "POST":
            if current_user.is_authenticated:
                comment = request.form.get('comment')
                if request.form.get('parent'):
                    new_comment = models.Comments(text=comment, game_id=game_id,
                                                  author_username=current_user.customer_username,
                                                  parent_id=int(request.form.get('parent')))
                elif request.form.get('edit'):
                    comment_id = int(request.form.get('edit'))
                    comment_object = models.Comments.query.filter_by(comment_id=comment_id).first()
                    comment_object.text = comment
                    comment_object.timestamp = datetime.now().replace(microsecond=0)
                    db.session.commit()
                    return redirect(request.url)
                else:
                    new_comment = models.Comments(text=comment, game_id=game_id,
                                                  author_username=current_user.customer_username)
                add_to_db(new_comment)
                return redirect(request.url)
        game_photo = models.GameImages.query.filter_by(game_id=game_id).first()
        game_comments = models.Comments.query.filter_by(game_id=game_id).order_by(models.Comments.comment_id).all()
        game_sub_comments = models.Comments.query.filter_by(game_id=game_id).filter(
            models.Comments.parent_id != None).order_by(models.Comments.comment_id).all()

        def time_after_comment(list_of_comments):
            comment_time_ago = []
            for comment_object in list_of_comments:
                comment_time_ago.append(humanize.precisedelta(datetime.now().replace(microsecond=0, second=0) - comment_object.timestamp.replace(microsecond=0, second=0)))
            return comment_time_ago
        game_sub_comments2 = time_after_comment(game_sub_comments)
        game_comments2 = time_after_comment(game_comments)
        comments_authors = [models.Customers.query.filter_by(customer_username=comment.author_username).order_by(
            models.Customers.customer_id).first()
                            for comment in game_comments
                            ]
        sub_comment_authors = [models.Customers.query.filter_by(customer_username=comment.author_username).order_by(
            models.Customers.customer_id).first()
                               for comment in game_sub_comments
                               ]

        def author_photos(list_of_authors: list):
            comment_author_images = []
            for author in list_of_authors:
                if author.customer_photo is not None:
                    comment_author_images.append(base64.b64encode(author.customer_photo).decode("utf-8"))
                else:
                    with open('./static/pngegg.png', 'rb') as default_photo:
                        comment_author_images.append(base64.b64encode(default_photo.read()).decode("utf-8"))
            return comment_author_images

        comment_authors_images = author_photos(comments_authors)
        sub_comment_authors_images = author_photos(sub_comment_authors)
        # НА ПЕРСПЕКТИВУ ЗРОБИТИ ПЛАТФОРМИ ТА ЇХ ВІДОБРАЖЕННЯ ІКОНОК
        # platforms_ico = models.Games.query.join(models.games_and_platforms).join(models.Platforms).filter((models.games_and_platforms.c.game_id == models.Games.game_id) & (models.games_and_platforms.c.platform_id == models.Platforms.platform_id)).all()
        # platforms_ico = [base64.b64encode(elem.platform_ico).decode("utf-8") for elem in game_details.platforms]
        game_image = convert_image_from_binary_to_unicode(game_photo.game_photo)
        try:
            g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
        except AttributeError:
            g.photo = None
        return render_template("game.html",
                               game_details=game_details,
                               game_image=game_image,
                               game_comments=game_comments,
                               game_comments2=game_comments2,
                               game_sub_comments=game_sub_comments,
                               game_sub_comments2=game_sub_comments2,
                               comment_authors_images=comment_authors_images,
                               sub_comment_authors_images=sub_comment_authors_images,
                               user_photo=g.photo,
                               cart_item_count=g.cart)
    return redirect('/')


@app.route('/<int:game_id>/edit', methods=["GET", "POST"])
def edit_game(game_id: int):
    g.photo = convert_image_from_binary_to_unicode(models.Customers.query.get(current_user.get_id()).customer_photo)
    if admin_permission() == 2:
        return redirect(f'/{game_id}')
    else:
        game = models.Games.query.get(game_id)
        game_image = models.GameImages.query.filter_by(game_id=game_id).first()
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


@app.route('/hide_game', methods=["POST"])
@login_required
def hide_game():
    game_id = request.json
    game = models.Games.query.get(game_id)
    if game.is_active:
        game.is_active = False
    else:
        game.is_active = True
    db.session.commit()
    return 'Ok'


@app.route('/')
def display_all_games():
    if not current_user.is_authenticated:
        if 'cart' not in session:
            session['cart'], session['cart_game_id'] = [], []
    if admin_permission() == 2:
        all_games = models.Games.query.order_by(models.Games.game_id).filter_by(is_active=True).all()
    else:
        all_games = models.Games.query.order_by(models.Games.game_id).all()
    raw_game_images = [models.GameImages.query.filter_by(game_id=game.game_id).first() for game in all_games]
    game_images = [convert_image_from_binary_to_unicode(elem.game_photo) for elem in raw_game_images]
    try:
        g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
    except AttributeError:
        g.photo = None
    return render_template('all_games.html',
                           all_games=all_games,
                           game_images=game_images,
                           genres=return_genres(),
                           user_photo=g.photo,
                           cart_item_count=g.cart)


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_login = request.form.get('user_email')
        user_password = request.form.get('user_password')
        remember = True if request.form.get('remember') else False
        if user_login and user_password:
            user_credentials = models.Customers.query.filter_by(customer_email=user_login).first()
            if user_credentials and check_password_hash(user_credentials.customer_password, user_password):
                # if remember and 'email' not in request.cookies:
                #     response = make_response(redirect(url_for('display_all_games')))
                #     response.set_cookie('email', user_login, max_age=60*60*24*7)
                #     response.set_cookie('pwd', user_password, max_age=60*60*24*7)
                #     response.set_cookie('rem', 'checked', max_age=60*60*24*7)
                login_user(user_credentials, remember=remember)
                return redirect(url_for('display_all_games', user_photo=g.photo))
            flash('Incorrect password')
            return redirect('/' + '?showModal=' + 'true')
        flash('Please, fill both fields email and password')
        return redirect('/' + '?showModal=' + 'true')
    return redirect(url_for('display_all_games', user_photo=g.photo, cart_item_count=g.cart))


@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        new_user_first_name = request.form.get('first_name')
        new_user_last_name = request.form.get('last_name')
        new_user_login = request.form.get('email')
        new_user_username = request.form.get('user_name')
        new_user_password = request.form.get('password')
        new_user_password_verification = request.form.get('password_two')
        if not (
                new_user_first_name or new_user_last_name or new_user_login or new_user_password or new_user_password_verification):
            flash('Please, fill all the fields')
            return redirect('/' + '?showModalSignUp=' + 'true')
        elif new_user_password != new_user_password_verification:
            flash('Passwords not match')
            return redirect('/' + '?showModalSignUp=' + 'true')
        else:
            if new_user_password_verification == new_user_password:
                if models.Customers.query.filter_by(customer_email=new_user_login).first():
                    flash('A user with this email already exists')
                    return redirect('/' + '?showModalSignUp=' + 'true')
                elif models.Customers.query.filter_by(customer_username=new_user_username).first():
                    flash('Someone already has that username')
                    return redirect('/' + '?showModalSignUp=' + 'true')
                else:
                    hash_password = generate_password_hash(new_user_password)
                    new_user = models.Customers(customer_first_name=new_user_first_name,
                                                customer_last_name=new_user_last_name,
                                                customer_username=new_user_username,
                                                customer_email=new_user_login,
                                                customer_password=hash_password,
                                                role=models.Roles.query.get(2))
                    add_to_db(new_user)
                    login_user(new_user, remember=False)
                    return redirect(url_for('display_all_games', user_photo=g.photo, cart_item_count=g.cart))
    return redirect(url_for('display_all_games', user_photo=g.photo, cart_item_count=g.cart))


@app.route('/logout', methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    session.pop('cart', None)
    session.pop('cart_game_id', None)
    return redirect(url_for('display_all_games', cart_item_count=g.cart))


@app.route('/edit_profile', methods=["GET", "POST"])
@login_required
def edit_profile():
    g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
    if request.method == "POST":
        new_first_name = request.form.get('new_first_name')
        new_last_name = request.form.get('new_last_name')
        new_user_photo = request.files['new_user_ico'].read()
        if new_first_name and new_last_name:
            current_user.customer_first_name = new_first_name
            current_user.customer_last_name = new_last_name
            if new_user_photo:
                current_user.customer_photo = new_user_photo
        db.session.commit()
        return redirect(url_for('display_all_games'))
    return render_template('user_profile.html',
                           customer=current_user,
                           user_photo=g.photo,
                           cart_item_count=g.cart)


@app.route('/order', methods=["POST", "GET"])
def order():
    if admin_permission() == 2:
        if request.method == "POST":
            if current_user.is_authenticated:
                try:
                    cart = len(models.CartItem.query.filter_by(models.Cart.query.filter_by(
                        customer_id=current_user.customer_id, cart_status=True).order_by(models.Cart.date.desc()).first().all()))
                except AttributeError:
                    cart = None

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
                            game = models.Games.query.get(game)
                            game.quantity_available -= session['cart'][index][1]
                        db.session.commit()
                        session.pop('cart', None)
                        session.pop('cart_game_id', None)
                        flash('Thank you, we will send the game licenses to the email you wrote in the order form', 'success')
                        return redirect('/order' + '?showAlertOrder=' + 'true')
                elif current_user.is_authenticated:
                    user_cart = models.Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                        models.Cart.date.desc()).first()
                    print(user_cart)
                    print(user_cart.cart_status)
                    user_cart.cart_status = False
                    user_cart_items = models.CartItem.query.filter_by(cart_id=user_cart.cart_id).all()
                    for elem in user_cart_items:
                        game = models.Games.query.get(elem.game_id)
                        game.quantity_available -= elem.amount
                    if models.Orders.query.filter_by(cart_id=user_cart.cart_id).first():
                        flash('You have no products added in your Shopping Cart', 'danger')
                        return redirect('/order' + '?showAlertOrder=' + 'true')
                    new_order = models.Orders(cart_id=user_cart.cart_id,
                                              customer_first_name=order_first_name,
                                              customer_last_name=order_last_name,
                                              customer_email=order_email,
                                              customer_phone=order_phone,
                                              payment_type=payment_type,
                                              comment=comment)
                    add_to_db(new_order)
                    flash('Thank you, we will send the game licenses to the email you wrote in the order form', 'success')
                    return redirect('/order' + '?showAlertOrder=' + 'true')
        return render_template('order.html', user_photo=g.photo, cart_item_count=g.cart)
    return redirect('/')


@app.route('/cart', methods=["POST", "GET"])
def cart():
    if not current_user.is_authenticated:
        if 'cart' in session:
            cart_items = session['cart']
            game_details = [models.Games.query.get(item) for item in session['cart_game_id']]
            cart_items_images = [convert_image_from_binary_to_unicode(
                models.GameImages.query.filter_by(game_id=elem).first().game_photo) for elem in session['cart_game_id']]
        else:
            return render_template('cart.html', user_photo=g.photo, cart_item_count=g.cart)
    elif current_user.is_authenticated:
        if admin_permission() == 1:
            return redirect('/')
        else:
            user_cart = models.Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                models.Cart.date.desc()).first()
            if user_cart.cart_status:
                cart_items = models.CartItem.query.filter_by(cart_id=user_cart.cart_id).order_by(
                    models.CartItem.cart_item_id).all()
                cart_items_images = [convert_image_from_binary_to_unicode(
                    models.GameImages.query.filter_by(game_id=elem.game_id).first().game_photo) for elem in cart_items]
                game_details = [models.Games.query.get(item.game_id) for item in cart_items]
            else:
                return render_template('cart.html', user_photo=g.photo, cart_item_count=g.cart)
    return render_template('cart.html',
                           cart_items=cart_items,
                           cart_items_images=cart_items_images,
                           game_details=game_details,
                           cart_item_count=g.cart,
                           user_photo=g.photo)


@app.route('/ajax_add_to_cart', methods=["POST"])
def ajax_add_to_cart():
    if request.method == "POST":
        game = models.Games.query.get(int(request.json))
        if not current_user.is_authenticated:
            if request.json not in session['cart_game_id']:
                session['cart'].append([float(game.price), 1])
                session['cart_game_id'].append(request.json)
            else:
                cart_id = session['cart_game_id'].index(request.json)
                session['cart'][cart_id][1] += 1
        else:
            if current_user.role_id == 2:
                if is_cart_active():
                    user_cart = models.Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                        models.Cart.date.desc()).first()
                    cart_items = models.CartItem.query.filter_by(cart_id=user_cart.cart_id).all()
                    cart_items_id = [item.game_id for item in cart_items]
                    if request.json in cart_items_id:
                        game_index = cart_items_id.index(request.json)
                        cart_items[game_index].amount += 1
                        cart_items[game_index].price = cart_items[game_index].amount * game.price
                        db.session.commit()
                    else:
                        new_cart_item = models.CartItem(game_id=request.json, price=game.price,
                                                        cart_id=user_cart.cart_id)
                        add_to_db(new_cart_item)
                        cart_items.append(new_cart_item)
                elif not is_cart_active():
                    user_cart = models.Cart(customer_id=current_user.customer_id)
                    add_to_db(user_cart)
                    new_cart_item = models.CartItem(game_id=int(request.json), price=game.price,
                                                    cart_id=user_cart.cart_id)
                    add_to_db(new_cart_item)
    return str(len(session['cart'])) if not current_user.is_authenticated \
        else str(len(models.CartItem.query.filter_by(cart_id=user_cart.cart_id).all()))


@app.route('/ajax_delete_from_cart', methods=["POST"])
def ajax_delete_from_cart():
    if request.method == "POST":
        game = models.Games.query.get(int(request.json))
        if not current_user.is_authenticated:
            cart_id = session['cart_game_id'].index(request.json)
            if session['cart'][cart_id][1] > 1:
                session['cart'][cart_id][1] -= 1
        elif current_user.is_authenticated:
            if admin_permission() == 2:
                user_cart = models.Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                    models.Cart.date.desc()).first()
                if user_cart.cart_status:
                    cart_items = models.CartItem.query.filter_by(cart_id=user_cart.cart_id).all()
                    cart_items_id = [item.game_id for item in cart_items]
                    game_index = cart_items_id.index(request.json)
                    if cart_items[game_index].amount > 1:
                        cart_items[game_index].amount -= 1
                        cart_items[game_index].price = cart_items[game_index].amount * game.price
                        db.session.commit()
    return str(len(session['cart'])) if not current_user.is_authenticated \
        else str(len(models.CartItem.query.filter_by(cart_id=user_cart.cart_id).all()))


@app.route('/ajax_delete_cart_item', methods=["POST"])
def ajax_delete_cart_item():
    if request.method == "POST":
        if not current_user.is_authenticated:
            cart_id = session['cart_game_id'].index(request.json)
            session['cart'].pop(cart_id)
            session['cart_game_id'].pop(cart_id)
        elif current_user.is_authenticated:
            user_cart = models.Cart.query.filter_by(customer_id=current_user.customer_id).order_by(
                models.Cart.date.desc()).first()
            cart_item = models.CartItem.query.get(request.json)
            db.session.delete(cart_item)
            db.session.commit()
    return str(len(session['cart'])) if not current_user.is_authenticated \
        else str(len(models.CartItem.query.filter_by(cart_id=user_cart.cart_id).all()))


@manager.user_loader
def load_user(customer_id):
    if customer_id is not None:
        return models.Customers.query.get(customer_id)
    return None


@app.before_request
def load_users():
    if current_user.is_authenticated:
        try:
            g.user = current_user.get_id()
            g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
            g.cart_id = models.Cart.query.filter_by(customer_id=g.user).order_by(
                models.Cart.date.desc()).first()
            if g.cart_id.cart_status:
                g.cart = len(models.CartItem.query.filter_by(cart_id=g.cart_id.cart_id).all())
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
