#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import ARRAY

# from sqlalchemy import Column, String, Integer, Boolean, DateTime, ARRAY, ForeignKey

db = SQLAlchemy()
# TODO: connect to a local postgresql database
def create_app(app):
    app.config.from_object('config')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)
    return db
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, index=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=False)
    genres = db.Column(ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(), default='')
    
    #In order to work with the relationship as with Query, lazy='dynamic'
    shows = db.relationship("Show", backref='Venues', lazy='dynamic')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
      return f'<Venue ID: {self.id}, Name: {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artists'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False, index=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=False)
    genres = db.Column(ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(), default='')

    shows = db.relationship("Show", backref='Artists', lazy='dynamic')
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    
    def __repr__(self):
      return f'<Artist ID: {self.id}, Name: {self.name}>'

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Shows'
    id = db.Column(db.Integer, primary_key=True, index=True)
    venue_id = db.Column(db.ForeignKey("Venues.id"), nullable=False)
    artist_id = db.Column(db.ForeignKey("Artists.id"), nullable=False)
    start_time = db.Column(db.DateTime)
    artists = db.relationship("Artist")

    def __repr__(self):
      return f'<Show venue_id: {self.venue_id}, artist_id: {self.artist_id}>'