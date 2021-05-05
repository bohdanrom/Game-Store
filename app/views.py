import base64
import datetime

from flask import render_template, request, redirect, flash, url_for, session, g
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
        user_role = models.Customers.query.filter_by(customer_id=g.user).first().role.name
    except AttributeError:
        user_role = 'Unauthorized User'
    return user_role


@app.after_request
def redirect_to_login_page(response):
    if response.status_code == 401:
        return redirect(url_for('login') + '?next=' + request.url)
    return response


@app.route('/add-game', methods=["GET", "POST"])
@login_required
def add_new_game():
    if 'User' in admin_permission():
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
            return redirect('#')
        game_genre = request.form.getlist('new_game_genre')
        game_description = request.form.get('new_game_description')
        game_image = request.files['new_game_ico'].read()
        new_game = models.Games(game_name=game_name,
                                game_description=game_description,
                                price=game_price)
        for genre in return_genres():
            if genre.game_type_name in game_genre:
                new_game.genres.append(genre)
        db.session.add(new_game)
        db.session.commit()
        if not game_image:
            with open('./static/mark_edited2.png', 'rb') as default_photo:
                game_image = default_photo.read()
        new_game_image = models.GameImages(game_id=new_game.game_id,
                                           game_photo=game_image)
        db.session.add(new_game_image)
        db.session.commit()
        return redirect(url_for('display_all_games'))
    return render_template('add_game.html', user_photo=g.photo, genres=return_genres())


@app.route('/delete_comment', methods=["POST"])
@login_required
def delete_comment():
    comment_id = request.json
    comment = models.Comments.query.get(int(comment_id))
    if comment.author_username == current_user.customer_username or admin_permission() == "Admin":
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
                    comment_object.timestamp = datetime.datetime.utcnow()
                    db.session.commit()
                    return redirect(request.url)
                else:
                    new_comment = models.Comments(text=comment, game_id=game_id,
                                                  author_username=current_user.customer_username)
                db.session.add(new_comment)
                db.session.commit()
                return redirect(request.url)
        game_photo = models.GameImages.query.filter_by(game_id=game_id).first()
        game_comments = models.Comments.query.filter_by(game_id=game_id).order_by(models.Comments.comment_id).all()
        game_sub_comments = models.Comments.query.filter_by(game_id=game_id).filter(
            models.Comments.parent_id != None).order_by(models.Comments.comment_id).all()
        comments_authors = [models.Customers.query.filter_by(customer_username=comment.author_username).order_by(models.Customers.customer_id).first()
                            for comment in game_comments
                            ]
        sub_comment_authors = [models.Customers.query.filter_by(customer_username=comment.author_username).order_by(models.Customers.customer_id).first()
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
                               login=g.admin_perm,
                               game_comments=game_comments,
                               game_sub_comments=game_sub_comments,
                               comment_authors_images=comment_authors_images,
                               sub_comment_authors_images=sub_comment_authors_images,
                               user_photo=g.photo)
    return redirect('/')


@app.route('/edit/<int:game_id>', methods=["GET", "POST"])
def edit_game(game_id: int):
    if 'User' in admin_permission():
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
                return redirect('#')
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
            return redirect("/")
        return render_template('add_game.html',
                               game=game,
                               game_image=game_image,
                               user_photo=g.photo,
                               genres=return_genres())


@app.route('/hide_game', methods=["POST"])
@login_required
def hide_game():
    if 'User' in admin_permission():
        return redirect('/')
    else:
        game_id = request.json
        game = models.Games.query.get(game_id)
        if game.is_active:
            game.is_active = False
        else:
            game.is_active = True
        db.session.commit()


@app.route('/')
def display_all_games():
    if 'User' in admin_permission():
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
                           login=g.admin_perm,
                           user_photo=g.photo)


# =========================================


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_login = request.form.get('user_email')
        user_password = request.form.get('user_password')
        if user_login and user_password:
            user_credentials = models.Customers.query.filter_by(customer_email=user_login).first()
            if user_credentials and check_password_hash(user_credentials.customer_password, user_password):
                login_user(user_credentials)
                session['customer_first_name'] = user_credentials.customer_first_name
                session['customer_last_name'] = user_credentials.customer_last_name
                # next_page = request.args.get('next')
                # return redirect(next_page)
                return redirect(url_for('display_all_games', user_photo=g.photo))
            return redirect('/login')
        else:
            flash('Please, fill both fields email and password')
        return redirect(url_for('display_all_games'))
    return redirect(url_for('display_all_games', user_photo=g.photo))


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
        elif new_user_password != new_user_password_verification:
            flash('Passwords not match')
        else:
            if new_user_password_verification == new_user_password:
                hash_password = generate_password_hash(new_user_password)
                new_user = models.Customers(customer_first_name=new_user_first_name,
                                            customer_last_name=new_user_last_name,
                                            customer_username=new_user_username,
                                            customer_email=new_user_login,
                                            customer_password=hash_password,
                                            role=models.Roles.query.get(2))
                db.session.add(new_user)
                db.session.commit()
                session['customer_first_name'] = new_user.customer_first_name
                session['customer_last_name'] = new_user.customer_last_name
                login_user(new_user)
                return redirect(url_for('display_all_games', user_photo=g.photo))
    return redirect(url_for('display_all_games', user_photo=g.photo))


@app.route('/logout', methods=["POST", "GET"])
@login_required
def logout():
    session.pop('customer_first_name', None)
    session.pop('customer_last_name', None)
    logout_user()
    return redirect(url_for('display_all_games'))


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
        session['customer_first_name'] = current_user.customer_first_name
        session['customer_last_name'] = current_user.customer_last_name
        session.modified = True
        return redirect(url_for('display_all_games'))
    return render_template('user_profile.html',
                           customer=current_user,
                           user_photo=g.photo)


@app.route('/order', methods=["POST", "GET"])
def order():
    if request.method == "POST":
        order_first_name = request.form.get("order_first_name")
        order_last_name = request.form.get("order_last_name")
        order_email = request.form.get("order_email")
        order_phone = request.form.get("order_phone")
        payment_type = request.form.get("payment_type")
        comment = request.form.get("Comment")
        print(order_first_name, order_last_name, order_email, order_phone, payment_type, comment)
    return render_template('cart.html')

@manager.user_loader
def load_user(customer_id):
    if customer_id is not None:
        return models.Customers.query.get(customer_id)
    return None


@manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page.')
    return redirect(url_for('display_all_games'))


@app.before_request
def load_users():
    if current_user.is_authenticated:
        try:
            g.user = current_user.get_id()
            g.admin_perm = current_user.role.name
            g.photo = convert_image_from_binary_to_unicode(current_user.customer_photo)
        except AttributeError:
            g.user = None
            g.admin_perm = None
            g.photo = None
    else:
        g.user = None
        g.admin_perm = None
        g.photo = None


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
