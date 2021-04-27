import base64

from flask import render_template, request, redirect, jsonify

from app import app, db, models


def return_genres():
    genres = models.GameGenres.query.all()
    return genres


@app.route('/add-game', methods=["GET", "POST"])
def add_new_game():
    if request.method == 'POST':
        game_name = request.form.get('new_game_name')
        game_price = float(request.form.get('new_game_price'))
        game_genre = request.form.getlist('new_game_genre')
        game_description = request.form.get('new_game_description')
        game_image = request.files['new_game_ico'].read()
        new_game = models.Games(game_name=game_name,
                                   game_description=game_description,
                                   price=game_price)
        for genre in models.GameGenres.query.all():
            if genre.game_type_name in game_genre:
                new_game.genres.append(genre)
        db.session.add(new_game)
        db.session.commit()
        new_game_image = models.GameImages(game_id=new_game.game_id,
                                              game_photo=game_image)
        db.session.add(new_game_image)
        db.session.commit()
        return render_template('add_game.html')
    return render_template('add_game.html', genres=return_genres())


@app.route('/<int:game_id>', methods=["GET", "POST"])
def display_game(game_id: int):
    game_details = models.Games.query.filter_by(game_id=game_id).first()
    game_photo = models.GameImages.query.filter_by(game_id=game_id).first()
    # НА ПЕРСПЕКТИВУ ЗРОБИТИ ПЛАТФОРМИ ТА ЇХ ВІДОБРАЖЕННЯ ІКОНОК
    # platforms_ico = models.Games.query.join(models.games_and_platforms).join(models.Platforms).filter((models.games_and_platforms.c.game_id == models.Games.game_id) & (models.games_and_platforms.c.platform_id == models.Platforms.platform_id)).all()
    # platforms_ico = [base64.b64encode(elem.platform_ico).decode("utf-8") for elem in game_details.platforms]
    game_image = base64.b64encode(game_photo.game_photo).decode("utf-8")

    if request.method == "POST":
        # file = request.files['file'].read()
        # file_name = form.name.data
        print("POST-method")
        return render_template("main-page.html")
    return render_template("game.html",
                           game_details=game_details,
                           game_image=game_image,
                           )


@app.route('/<int:game_id>/edit', methods=["GET", "POST"])
def edit_game(game_id: int):
    game = models.Games.query.get(game_id)
    game_image = models.GameImages.query.filter_by(game_id=game_id).first()
    if request.method == "POST":
        game.game_name = request.form.get('new_game_name')
        game.price = float(request.form.get('new_game_price'))
        game_genres = request.form.getlist('new_game_genre')
        game.game_description = request.form.get('new_game_description')
        game_image.game_photo = request.files['new_game_ico'].read()
        if game_genres:
            game.genres.clear()
            for genre in models.GameGenres.query.all():
                if genre.game_type_name in game_genres:
                    game.genres.append(genre)
        db.session.commit()
        return redirect("/")
    return render_template('add_game.html', game=game, game_image=game_image, genres=return_genres())


@app.route('/')
def display_all_games():
    all_games = models.Games.query.order_by(models.Games.game_id).all()
    raw_game_images = models.GameImages.query.order_by(models.GameImages.game_id).all()
    game_images = [base64.b64encode(elem.game_photo).decode("utf-8") for elem in raw_game_images]
    return render_template('all_games.html', all_games=all_games, game_images=game_images, genres=return_genres())


@app.route('/search', methods=["POST"])
def search():
    game_name = request.form['game_name']
    search = f"%{game_name}%"
    raw_all_games = models.Games.query.filter(models.Games.game_name.like(search)).all()
    game_ids, all_games = [], []
    for game in raw_all_games:
        game_ids.append(game.game_id)
        all_games.append(game.as_dict())
    raw_game_images = models.GameImages.query.order_by(models.GameImages.game_id in game_ids).all()
    for index, element in enumerate(all_games):
        element['game_image'] = base64.b64encode(raw_game_images[index].game_photo).decode("utf-8")
    if all_games:
        return jsonify(all_games)
    return jsonify(error=404)

#=========================================
@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_login = request.form.get('user_email')
        user_password = request.form.get('user_password')
        print(user_login, user_password)
    return 'Login'


@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        new_user_first_name = request.form.get('first_name')
        new_user_last_name = request.form.get('last_name')
        new_user_login = request.form.get('email')
        new_user_password = request.form.get('password')
        new_user_password_verification = request.form.get('password_two')
        print(new_user_first_name, new_user_last_name, new_user_login, new_user_login, new_user_password, new_user_password_verification)
    return 'signUp'


@app.route('/logout')
def logout():
    return 'Logout'


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
