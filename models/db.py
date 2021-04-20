from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


# game_and_game_types = db.Table('Games_and_Game_Types',
#     db.Column('game_id', db.Integer, db.ForeignKey('games.game_id')),
#     db.Column('game_type_id', db.Integer, db.ForeignKey('game_types.game_type_id'))
# )


# games_and_platforms = db.Table('Games_and_Platforms',
#     db.Column('game_id', db.Integer, db.ForeignKey('games.game_id')),
#     db.Column('platform_id', db.Integer, db.ForeignKey('platforms.platform_id'))
# )


class Games(db.Model):
    game_id = db.Column(db.Integer, primary_key=True, nullable=False)
    game_name = db.Column(db.String, nullable=False)
    game_description = db.Column(db.Text, nullable=False)
    release_date = db.Column(db.DateTime, nullable=False)
    number_of_players = db.Column(db.Integer)
    quantity_available = db.Column(db.Integer)
    price = db.Column(db.Numeric(5, 2))
    # genres = db.relationship('GameTypes',
    #                          secondary=game_and_game_types,
    #                          backref=db.backref('game_genres', lazy='joined'))
    # platforms = db.relationship('Platforms',
    #                          secondary=games_and_platforms,
    #                          backref=db.backref('game_platforms', lazy='joined'))


class GameImages(db.Model):
    game_id = db.Column(db.Integer)
    game_image_id = db.Column(db.Integer, primary_key=True, nullable=False)
    game_photo = db.Column(db.BLOB, nullable=False)


class Platforms(db.Model):
    platform_id = db.Column(db.Integer, primary_key=True, nullable=False)
    platform_name = db.Column(db.VARCHAR(255), nullable=False)


class GameTypes(db.Model):
    game_type_id = db.Column(db.Integer, primary_key=True, nullable=False)
    game_type_name = db.Column(db.VARCHAR(255), nullable=False)

