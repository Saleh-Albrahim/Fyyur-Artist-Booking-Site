from app import db
from sqlalchemy.types import PickleType


class Locations(db.Model):
    __tablename__ = 'locations'
    __table_args__ = (db.UniqueConstraint('city', 'state'),)
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120), primary_key=True)
    state = db.Column(db.String(120), primary_key=True)
    venues = db.relationship('venues', backref='location')
    artist = db.relationship('artist', backref='location')


class Show(db.Model):
    __tablename__ = 'show'
    artist_ID = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), primary_key=True)
    venue_ID = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), primary_key=True)
    start_time = db.Column(db.DateTime)


class Venues(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    Location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    genres = db.Column(PickleType)
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.Boolean)
    facebook_link = db.Column(db.String(120))
    show = db.relationship('show', backref='venue')


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    Location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(PickleType)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    show = db.relationship('show', backref='artist')
