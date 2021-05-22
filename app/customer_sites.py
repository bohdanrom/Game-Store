import base64
from datetime import datetime

import humanize
from flask_login import login_required, current_user
from flask import Blueprint, request, redirect, g, render_template, session, url_for

from app import db
from models import Comments, Games, GameImages, Customers
from views import admin_permission, add_to_db, convert_image_from_binary_to_unicode, return_genres


customer_sites = Blueprint("customer_sites", __name__)


@customer_sites.route('/delete_comment', methods=["POST"])
@login_required
def delete_comment():
    comment_id = request.json
    comment = Comments.query.get(int(comment_id))
    if comment.author_username == current_user.customer_username or admin_permission() == 1:
        db.session.delete(comment)
        db.session.commit()
    return "Ok"


@customer_sites.route('/<int:game_id>', methods=["GET", "POST"])
def display_game(game_id: int):
    game_details = Games.query.filter_by(game_id=game_id).first()
    if game_details.is_active:
        if request.method == "POST":
            if current_user.is_authenticated:
                comment = request.form.get('comment')
                if request.form.get('parent'):
                    new_comment = Comments(text=comment, game_id=game_id,
                                                  author_username=current_user.customer_username,
                                                  parent_id=int(request.form.get('parent')))
                elif request.form.get('edit'):
                    comment_id = int(request.form.get('edit'))
                    comment_object = Comments.query.filter_by(comment_id=comment_id).first()
                    comment_object.text = comment
                    db.session.commit()
                    return redirect(request.url)
                else:
                    new_comment = Comments(text=comment, game_id=game_id,
                                                  author_username=current_user.customer_username)
                add_to_db(new_comment)
                return redirect(request.url)
        game_photo = GameImages.query.filter_by(game_id=game_id).first()
        game_comments = Comments.query.filter_by(game_id=game_id).order_by(Comments.comment_id).all()
        game_sub_comments = Comments.query.filter_by(game_id=game_id).filter(Comments.parent_id is not None)\
            .order_by(Comments.comment_id).all()


        def time_after_comment(list_of_comments):
            comment_time_ago = []
            for comment_object in list_of_comments:
                comment_time_ago.append(
                    humanize.precisedelta(datetime.utcnow().replace(microsecond=0, second=0) -
                                          comment_object.timestamp.replace(microsecond=0, second=0)))
            return comment_time_ago
        game_sub_comments2 = time_after_comment(game_sub_comments)
        game_comments2 = time_after_comment(game_comments)
        comments_authors = [Customers.query.filter_by(customer_username=comment.author_username).order_by(
            Customers.customer_id).first()
                            for comment in game_comments]
        sub_comment_authors = [Customers.query.filter_by(customer_username=comment.author_username).order_by(
            Customers.customer_id).first()
                               for comment in game_sub_comments]


        def author_photos(list_of_authors: list):
            comment_author_images = []
            for author in list_of_authors:
                if author.customer_photo is not None:
                    comment_author_images.append(base64.b64encode(author.customer_photo).decode("utf-8"))
                else:
                    with open('static/images/pngegg.png', 'rb') as default_photo:
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


@customer_sites.route('/')
def display_all_games():
    if not current_user.is_authenticated:
        if 'cart' not in session:
            session['cart'], session['cart_game_id'] = [], []
    if admin_permission() == 2:
        all_games = Games.query.order_by(Games.game_id).filter_by(is_active=True).all()
    else:
        all_games = Games.query.order_by(Games.game_id).all()
    raw_game_images = [GameImages.query.filter_by(game_id=game.game_id).first() for game in all_games]
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


@customer_sites.route('/edit_profile', methods=["GET", "POST"])
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
        return redirect(url_for('customer_sites.display_all_games'))
    return render_template('user_profile.html',
                           customer=current_user,
                           user_photo=g.photo,
                           cart_item_count=g.cart)
