from datetime import date

from flask_login import UserMixin

from . import db, manager


games_and_game_genres = db.Table(
    'games_and_game_genres',
    db.Column('game_id', db.Integer, db.ForeignKey('games.game_id')),
    db.Column('game_type_id', db.Integer, db.ForeignKey('game_genres.game_type_id'))
)


games_and_platforms = db.Table(
    'games_and_platforms',
    db.Column('game_id', db.Integer, db.ForeignKey('games.game_id')),
    db.Column('platform_id', db.Integer, db.ForeignKey('platforms.platform_id'))
)


class Mixin():
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Games(db.Model, Mixin):
    __tablename__ = 'games'
    game_id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(100), nullable=False, unique=True)
    game_description = db.Column(db.Text, nullable=False)
    release_date = db.Column(db.Date, nullable=False, default=date.today())
    number_of_players = db.Column(db.Integer, default=0)
    quantity_available = db.Column(db.Integer, default=2000)
    price = db.Column(db.Numeric(5, 2))
    genres = db.relationship("GameGenres", secondary=games_and_game_genres,
                             lazy='subquery', backref=db.backref('classes', lazy=True))
    platforms = db.relationship("Platforms", secondary=games_and_platforms,
                                lazy='subquery', backref=db.backref('classes', lazy=True))


class GameImages(db.Model, Mixin):
    __tablename__ = 'game_images'
    game_id = db.Column(db.Integer, db.ForeignKey('games.game_id'))
    game_image_id = db.Column(db.Integer, primary_key=True)
    game_photo = db.Column(db.LargeBinary, nullable=False)
    game = db.relationship("Games", backref=db.backref("games", uselist=False))


class Platforms(db.Model, Mixin):
    __tablename__ = 'platforms'
    platform_id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String(50), nullable=False)
    platform_ico = game_photo = db.Column(db.LargeBinary, nullable=False)


class GameGenres(db.Model, Mixin):
    __tablename__ = 'game_genres'
    game_type_id = db.Column(db.Integer, primary_key=True)
    game_type_name = db.Column(db.String(50), nullable=False)


class Roles(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Customers(db.Model, UserMixin):
    __tablename__ = 'customers'
    customer_id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))
    customer_email = db.Column(db.String(128), unique=True, nullable=False)
    customer_password = db.Column(db.String(128), nullable=False)
    customer_photo = db.Column(db.LargeBinary)
    customer_first_name = db.Column(db.String(30))
    customer_last_name = db.Column(db.String(30))
    role = db.relationship("Roles", backref=db.backref('roles'), uselist=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.customer_id)


@manager.user_loader
def load_user(customer_id):
    return Customers.query.get(customer_id)