import base64
import jinja2
from flask import Flask, render_template, request
import models.db

app = Flask(__name__)
env = jinja2.Environment()


@app.route('/')
def main_page():
    return render_template('main-page.html')


@app.route('/<int:game_id>', methods=["GET", "POST"])
def display_game(game_id: int):
    game_details = models.db.Games.query.filter_by(game_id=game_id).first()
    game_photo = models.db.GameImages.query.filter_by(game_id=game_id).first()
    # НА ПЕРСПЕКТИВУ ЗРОБИТИ ПЛАТФОРМИ ТА ЇХ ВІДОБРАЖЕННЯ ІКОНОК
    # platforms_ico = models.db.Games.query.join(models.db.games_and_platforms).join(models.db.Platforms).filter((models.db.games_and_platforms.c.game_id == models.db.Games.game_id) & (models.db.games_and_platforms.c.platform_id == models.db.Platforms.platform_id)).all()
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

@app.route('/games')
def display_all_games():
    all_games = models.db.Games.query.order_by(models.db.Games.game_id).all()
    game_images = models.db.GameImages.query.order_by(models.db.GameImages.game_id).all()
    encoded_game_photos = [base64.b64encode(elem.game_photo).decode("utf-8") for elem in game_images]
    return render_template('all_games.html',
                           all_games=all_games,
                           game_images=encoded_game_photos)


if __name__ == '__main__':
    app.jinja_env.filters['zip'] = zip
    app.config['SECRET_KEY'] = 'random-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:BOGDAN12312r@localhost:5432/game_store2"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    models.db.db.init_app(app)
    app.run(debug=True, use_reloader=True)