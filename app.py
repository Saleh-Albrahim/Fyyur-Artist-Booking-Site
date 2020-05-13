#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#


import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy.types import PickleType

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db = SQLAlchemy(app)

Migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Locations(db.Model):
    __tablename__ = 'locations'
    __table_args__ = (db.UniqueConstraint('city', 'state'),)
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String())
    state = db.Column(db.String())
    venues = db.relationship(
        'Venues', backref='locations')
    artist = db.relationship(
        'Artist', backref='locations')

    def __repr__(self):
        return f' {self.city} {self.state}'


class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    artist_ID = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), nullable=False)
    venue_ID = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), nullable=False)
    start_time = db.Column(db.DateTime)

    def __repr__(self):
        return f' {self.artist_ID} {self.venue_ID} {self.start_time}'


class Venues(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    Location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=False)
    address = db.Column(db.String())
    phone = db.Column(db.String())
    image_link = db.Column(db.String())
    website = db.Column(db.String())
    genres = db.Column(PickleType)
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    facebook_link = db.Column(db.String())
    show = db.relationship('Show', backref='venues')

    def __repr__(self):
        return f' {self.name} {self.id}'


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    Location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=False)
    phone = db.Column(db.String())
    genres = db.Column(PickleType)
    image_link = db.Column(db.String())
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean)
    facebook_link = db.Column(db.String())
    seeking_description = db.Column(db.String())
    show = db.relationship('Show', backref='artist')

    def __repr__(self):
        return f' {self.id} {self.name} {self.Location_id} {self.website}'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    all_location = Locations.query.all()
    data = []
    for location in all_location:
        venues = Venues.query.filter_by(Location_id=location.id).all()
        venueList = []
        for v in venues:
            venueList.append({"id": v.id,
                              "name": v.name,
                              "num_upcoming_shows": len(Show.query.filter(Show.venue_ID == v.id)
                                                        .filter(Show.start_time >= datetime.now()).all())})
        data.append(
            {"city": location.city, "state": location.state, "venues": venueList})
    # num_shows should be aggregated based on number of upcoming shows per venue.

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term')
    # source https://stackoverflow.com/questions/3325467/
    tag = f"%{search_term}%"
    answers = Venues.query.filter(Venues.name.like(tag)).all()
    data = []
    for d in answers:
        data.append({
            "id": d.id,
            "name": d.name,
            "num_upcoming_shows": len(Show.query.filter(Show.venue_ID == d.id)
                                      .filter(Show.start_time >= datetime.now()).all())
        })
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    past_showsData = Show.query.with_entities(Show.artist_ID, Artist.name, Artist.image_link, Show.start_time).join(Artist).filter(
        Show.venue_ID == venue_id).filter(Show.start_time < datetime.now()).all()
    past_shows = []

    for p in past_showsData:
        past_shows.append({"artist_id": p.artist_ID,
                           "artist_name": p.name,
                           "artist_image_link": p.image_link,
                           "start_time": p.start_time.strftime("%Y-%m-%d %H:%M:%S")})

    upcoming_showsData = Show.query.with_entities(Show.artist_ID, Artist.name, Artist.image_link, Show.start_time).join(Artist).filter(
        Show.venue_ID == venue_id).filter(Show.start_time >= datetime.now()).all()

    upcoming_shows = []
    for u in upcoming_showsData:
        upcoming_shows.append({"artist_id": u.artist_ID,
                               "artist_name": u.name,
                               "artist_image_link": u.image_link,
                               "start_time": u.start_time.strftime("%Y-%m-%d %H:%M:%S")})
 # shows the venue page with the given venue_id

    v = Venues.query.join(Locations)\
        .filter(Venues.id == venue_id).filter(Locations.id == Venues.Location_id).first()

    new_venue = {
        "id": v.id,
        "name": v.name,
        "genres": v.genres,
        "address": v.address,
        "city": v.locations.city,
        "state": v.locations.state,
        "phone": v.phone,
        "website": v.website,
        "facebook_link": v.facebook_link,
        "seeking_talent": v.seeking_talent,
        "seeking_description": v.seeking_description,
        "image_link": v.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=new_venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook = request.form['facebook_link']
        website = request.form['website']
        image_link = request.form['image_link']
        if request.form['seeking_talent'] == 'y':
            seeking_talent = True
        else:
            seeking_talent = False
        seeking_description = request.form['seeking_description']

        # check if this city & state is added before if yes get the id
        getlocation = Locations.query.filter_by(city=city, state=state).first()
        if getlocation is None:
            newLocation = Locations(city=city, state=state)
            db.session.add(newLocation)
            db.session.commit()
            getlocation = Locations.query.filter_by(
                city=city, state=state).first()
        Location_id = getlocation.id

        # insert the new venue
        newVenues = Venues(name=name, Location_id=Location_id,
                           address=address, phone=phone, genres=genres, facebook_link=facebook,
                           website=website, image_link=image_link, seeking_talent=seeking_talent, seeking_description=seeking_description)
        db.session.add(newVenues)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + name + ' could not be listed.')
    else:
        flash('Venues was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
    error = False
    try:
        Venues.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close

    if error:
        flash('An error occurred. Venu  could not be Deleted.')
    else:
        flash('Venues was successfully Deleted!')
    return redirect(url_for('index'))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    v = Venues.query.join(Locations)\
        .filter(Venues.id == venue_id).filter(Locations.id == Venues.Location_id).first()
    form = VenueForm()
    venue = {
        "id": v.id,
        "name": v.name,
        "genres": v.genres,
        "address": v.address,
        "city": v.locations.city,
        "state": v.locations.state,
        "phone": v.phone,
        "website": v.website,
        "facebook_link": v.facebook_link,
        "seeking_talent": v.seeking_talent,
        "seeking_description": v.seeking_description,
        "image_link": v.image_link,
    }

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address: request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook = request.form['facebook_link']
    website = request.form['website']
    image_link = request.form['image_link']
    if request.form['seeking_talent'] == 'y':
        seeking_talent = True
    else:
        seeking_talent = False
    seeking_description = request.form['seeking_description']
    try:
        get_artists = Venues.query.get(venue_id)
        get_artists.name = name
        get_artists.phone = phone
        get_artists.genres = genres
        get_artists.facebook = facebook
        get_artists.website = website
        get_artists.image_link = image_link
        get_artists.seeking_talent = seeking_talent
        get_artists.seeking_description = seeking_description
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term')
    # source https://stackoverflow.com/questions/3325467/
    tag = f"%{search_term}%"
    answers = Artist.query.filter(Artist.name.like(tag)).all()
    data = []
    for d in answers:
        data.append({
            "id": d.id,
            "name": d.name,
            "num_upcoming_shows": len(Show.query.filter(Show.artist_ID == d.id)
                                      .filter(Show.start_time >= datetime.now()).all())
        })
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    past_showsData = Show.query.with_entities(Show.artist_ID, Venues.name, Venues.image_link, Show.start_time).join(Venues).filter(
        Show.artist_ID == artist_id).filter(Show.start_time < datetime.now()).all()
    past_shows = []

    for p in past_showsData:
        past_shows.append({"artist_ID": p.artist_ID,
                           "venue_name": p.name,
                           "venue_image_link": p.image_link,
                           "start_time": p.start_time.strftime("%Y-%m-%d %H:%M:%S")})

    upcoming_showsData = Show.query.with_entities(Show.artist_ID, Venues.name, Venues.image_link, Show.start_time).join(Venues).filter(
        Show.artist_ID == artist_id).filter(Show.start_time >= datetime.now()).all()

    upcoming_shows = []
    for u in upcoming_showsData:
        upcoming_shows.append({"artist_ID": u.artist_ID,
                               "venue_name": u.name,
                               "venue_image_link": u.image_link,
                               "start_time": u.start_time.strftime("%Y-%m-%d %H:%M:%S")})
 # shows the venue page with the given venue_id

    r = Artist.query.join(Locations)\
        .filter(Artist.id == artist_id).filter(Locations.id == Artist.Location_id).first()
    new_artist = {
        "id": r.id,
        "name": r.name,
        "genres": r.genres,
        "city": r.locations.city,
        "state": r.locations.state,
        "phone": r.phone,
        "website": r.website,
        "facebook_link": r.facebook_link,
        "seeking_venue": r.seeking_venue,
        "seeking_description": r.seeking_description,
        "image_link": r.image_link,
    }

    return render_template('pages/show_artist.html', artist=new_artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    r = Artist.query.join(Locations)\
        .filter(Artist.id == artist_id).filter(Locations.id == Artist.Location_id).first()
    artist = {
        "id": r.id,
        "name": r.name,
        "genres": r.genres,
        "city": r.locations.city,
        "state": r.locations.state,
        "phone": r.phone,
        "website": r.website,
        "facebook_link": r.facebook_link,
        "seeking_venue": r.seeking_venue,
        "seeking_description": r.seeking_description,
        "image_link": r.image_link,
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook = request.form['facebook_link']
    website = request.form['website']
    image_link = request.form['image_link']
    if request.form['seeking_venue'] == 'y':
        seeking_venue = True
    else:
        seeking_venue = False
    seeking_description = request.form['seeking_description']
    try:
        get_artists = Artist.query.get(artist_id)
        get_artists.name = name
        get_artists.city = city
        get_artists.state = state
        get_artists.phone = phone
        get_artists.genres = genres
        get_artists.facebook = facebook
        get_artists.website = website
        get_artists.image_link = image_link
        get_artists.seeking_venue = seeking_venue
        get_artists.seeking_description = seeking_description
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook = request.form['facebook_link']
        website = request.form['website']
        image_link = request.form['image_link']
        if request.form['seeking_venue'] == 'y':
            seeking_venue = True
        else:
            seeking_venue = False
        seeking_description = request.form['seeking_description']

        # check if this city & state is added before if yes get the id
        getlocation = Locations.query.filter_by(city=city, state=state).first()
        if getlocation is None:
            newLocation = Locations(city=city, state=state)
            db.session.add(newLocation)
            db.session.commit()
            getlocation = Locations.query.filter_by(
                city=city, state=state).first()
        Location_id = getlocation.id

        # insert the new artist
        newArtist = Artist(name=name, Location_id=Location_id,
                           phone=phone, genres=genres, facebook_link=facebook,
                           website=website, image_link=image_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
        db.session.add(newArtist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + name + ' could not be listed.')
    else:
        flash('Artist ' + name + ' was successfully listed!')

    return render_template('pages/home.html')


@app.route('/artists/<artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
    error = False
    try:
        Artist.query.filter_by(id=artist_id).delete()
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close

    if error:
        flash('An error occurred. Artist could not be Deleted.')
    else:
        flash('Artist was successfully Deleted!')
    return redirect(url_for('index'))
#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    showsData = Show.query.with_entities(Show.venue_ID, Venues.name.label('venues_name'), Show.artist_ID, Artist.name.label('artist_name'), Artist.image_link, Show.start_time).join(
        Artist).join(Venues).filter(Show.venue_ID == Venues.id).filter(Show.artist_ID == Venues.id).all()

    data = []
    for d in showsData:
        data.append({
            "venue_id": d.venue_ID,
            "venue_name": d.venues_name,
            "artist_id": d.artist_ID,
            "artist_name": d.artist_name,
            "artist_image_link": d.image_link,
            "start_time": d.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']
        show = Show(artist_ID=artist_id, venue_ID=venue_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run()
