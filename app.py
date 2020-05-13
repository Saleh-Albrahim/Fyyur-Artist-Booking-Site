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

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://Saleh:123@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

Migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Locations(db.Model):
    __tablename__ = 'locations'
    __table_args__ = (db.UniqueConstraint('city', 'state'),)
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120), primary_key=True)
    state = db.Column(db.String(120), primary_key=True)
    venues = db.relationship('Venues', backref='venues')
    artist = db.relationship('Artist', backref='artist')

    def __repr__(self):
        return f' {self.city} {self.state}'


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
    seeking_description = db.Column(db.String(800))
    facebook_link = db.Column(db.String(120))
    show = db.relationship('Show', backref='venue')

    def __repr__(self):
        return f' {self.name} {self.id}'


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    Location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(PickleType)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    facebook_link = db.Column(db.String(120))
    seeking_description = db.Column(db.String(800))
    show = db.relationship('Show', backref='artist')
# TODO: implement any missing fields, as a database migration using Flask-Migratef

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

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
    # TODO: replace with real venues data.
    all_location = Locations.query.all()
    data = []
    for location in all_location:
        venues = Venues.query.filter_by(Location_id=location.id).all()
        venueList = []
        for v in venues:
            venueList.append({"id": v.id,
                              "name": v.name,
                              "num_upcoming_shows": len(Show.query.filter(Show.venue_ID == v.id)
                                                        .filter(Show.start_time > datetime.now()).all())})
        data.append(
            {"city": location.city, "state": location.state, "venues": venueList})
    # num_shows should be aggregated based on number of upcoming shows per venue.

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        "count": 1,
        "data": [{
            "id": 2,
            "name": "The Dueling Pianos Bar",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    # shows the venue page with the given venue_id
    v = Venues.query.join(Locations)\
        .filter(Venues.Location_id == Locations.id).filter(Venues.id == venue_id).first()

    past_showsData = Show.query.filter_by(venue_ID=venue_id)\
        .filter(Show.start_time < datetime.now()).join(Artist).all()
    past_shows = []

    for p in past_showsData:
        past_shows.append({"artist_id": p.artist.id,
                           "artist_name": p.artist.name,
                           "artist_image_link": p.image_link,
                           "start_time": p.start_time})

    upcoming_showsData = Show.query.filter_by(venue_ID=venue_id)\
        .filter(Show.start_time >= datetime.now()).join(Artist).all()

    upcoming_shows = []
    for u in upcoming_showsData:
        past_shows.append({"artist_id": p.artist.id,
                           "artist_name": p.name,
                           "artist_image_link": p.image_link,
                           "start_time": p.start_time})

    new_venue = {
        "id": v.id,
        "name": v.name,
        "genres": v.genres,
        "address": v.address,
        "city": v.city,
        "state": v.state,
        "phone": v.phone,
        "website": v.website,
        "facebook_link": v.facebook_link,
        "seeking_talent": v.seeking_talent,
        "seeking_description": v.seeking_description,
        "image_link": v.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_showsData,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_showsData),
    }

    data = list(filter(lambda d: d['id'] ==
                       venue_id, [data2, data3]))[0]
    return render_template('pages/show_venue.html', venue=data)

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
        print("city here", getlocation)
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
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + name + ' could not be listed.')
    else:
        flash('Venues was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = [{
        "id": 4,
        "name": "Guns N Petals",
    }, {
        "id": 5,
        "name": "Matt Quevedo",
    }, {
        "id": 6,
        "name": "The Wild Sax Band",
    }]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "count": 1,
        "data": [{
            "id": 4,
            "name": "Guns N Petals",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    data1 = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "past_shows": [{
            "venue_id": 1,
            "venue_name": "The Musical Hop",
            "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
            "start_time": "2019-05-21T21:30:00.000Z"
        }],
        "upcoming_shows": [],
        "past_shows_count": 1,
        "upcoming_shows_count": 0,
    }
    data2 = {
        "id": 5,
        "name": "Matt Quevedo",
        "genres": ["Jazz"],
        "city": "New York",
        "state": "NY",
        "phone": "300-400-5000",
        "facebook_link": "https://www.facebook.com/mattquevedo923251523",
        "seeking_venue": False,
        "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "past_shows": [{
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2019-06-15T23:00:00.000Z"
        }],
        "upcoming_shows": [],
        "past_shows_count": 1,
        "upcoming_shows_count": 0,
    }
    data3 = {
        "id": 6,
        "name": "The Wild Sax Band",
        "genres": ["Jazz", "Classical"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "432-325-5432",
        "seeking_venue": False,
        "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "past_shows": [],
        "upcoming_shows": [{
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2035-04-01T20:00:00.000Z"
        }, {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2035-04-08T20:00:00.000Z"
        }, {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2035-04-15T20:00:00.000Z"
        }],
        "past_shows_count": 0,
        "upcoming_shows_count": 3,
    }
    data = list(filter(lambda d: d['id'] ==
                       artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

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

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = [{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
    }]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
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
