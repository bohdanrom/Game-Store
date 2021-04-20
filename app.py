import json
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
    # game_genres = models.db.Games.query.join(models.db.game_and_game_types).join(models.db.GameTypes).filter((models.db.game_and_game_types.c.game_id == models.db.Games.game_id) & (models.db.game_and_game_types.c.game_type_id == models.db.GameTypes.game_type_id)).all()
    game_genres = models.db.db.session.execute("SELECT gt.game_type_name, gatp.game_id FROM Games g "
                                            "INNER JOIN Games_and_Game_Types gatp on g.game_id = gatp.game_id "
                                            "INNER JOIN Game_Types gt on gatp.game_type_id = gt.game_type_id "
                                            "WHERE gatp.game_id = :game_id", {'game_id': game_id})
    game_platforms = models.db.db.session.execute("SELECT p.platform_name, gap.game_id, p.platform_ico "
                                               "FROM Games g INNER JOIN Games_and_Platforms gap on g.game_id = gap.game_id "
                                               "INNER JOIN Platforms p on gap.platform_id = p.platform_id "
                                               "WHERE gap.game_id = :game_id", {'game_id': game_id})
    platforms_ico = [base64.b64encode(elem[2]).decode("utf-8") for elem in game_platforms]
    game_image = base64.b64encode(game_photo.game_photo).decode("utf-8")

    # result_json = {'gameImage': f'{game_image}', 'gameName', 'gamePrice', 'gameGenres', 'gamePlatforms', 'gameDescription'}

    if request.method == "POST":
        # file = request.files['file'].read()
        # file_name = form.name.data
        print("POST-method")
        return render_template("main-page.html")
    return render_template("game.html",
                           game_details=game_details,
                           game_genres=game_genres,
                           game_platforms=game_platforms,
                           platforms_ico=platforms_ico,
                           game_image=game_image
                           )

@app.route('/games')
def display_all_games():
    all_games = models.db.Games.query.all()
    print(all_games)
    game_photos = models.db.GameImages.query.all()
    game_genres = models.db.db.session.execute("SELECT g.game_name, gatp.game_type_id, gt.game_type_name, gatp.game_id "
                                               "FROM Games g INNER JOIN Games_and_Game_Types gatp on g.game_id = gatp.game_id "
                                               "INNER JOIN Game_Types gt on gatp.game_type_id = gt.game_type_id ")
    encoded_game_photos = [base64.b64encode(elem.game_photo).decode("utf-8") for elem in game_photos]
    print(len(encoded_game_photos))
    # game_data = models.db.db.session.execute("SELECT g.game_name, g.price, gt.game_type_name, gatp.game_id "
    #                                          "FROM Games g INNER JOIN Games_and_Game_Types gatp on g.game_id = gatp.game_id "
    #                                          "INNER JOIN Game_Types gt on gatp.game_type_id = gt.game_type_id "
    #                                          "INNER JOIN Game_Images gi on g.game_id = gi.game_id")

    return render_template('all_games.html', all_games=all_games, game_genres=game_genres, game_photos=encoded_game_photos)
   # game_photos=encoded_game_photos,
   # game_genres=game_genres)
   # game_data=game_data)


def init_db():
    """ this function create database and all tables in it """
    models.db.db.app = app
    models.db.db.create_all()


if __name__ == '__main__':
    app.jinja_env.filters['zip'] = zip
    app.config['SECRET_KEY'] = 'random-secret-key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    models.db.db.init_app(app)
    init_db()
    app.run(debug=True, use_reloader=True)