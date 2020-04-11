#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    # artist = db.relationship('Artist', secondary='show', backref=db.backref('venues', lazy=True))
    shows = db.relationship('Show', backref='venue', lazy=True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# # # TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.TIMESTAMP, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)

# #----------------------------------------------------------------------------#
# # Filters.
# #----------------------------------------------------------------------------#


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
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = []

    # This returns unique city/state combinations in the format:
    # [(city1,state1), (city2,state2)]
    city_states = db.session.query(Venue.city, Venue.state).group_by(
        Venue.city, Venue.state).all()

    # Loop through each city_state
    for city_state in city_states:
        # city_state is a tuple of (cityname, statename)

        city_data = {}
        city_data['city'] = city_state[0]
        city_data['state'] = city_state[1]
        city_data['venues'] = []

        # Fetch all venues located in this city and state
        venues = db.session.query(Venue).filter(
            Venue.city == city_state[0]).filter(Venue.state == city_state[1])

        for venue in venues:
            venue_data = {}
            venue_data['id'] = venue.id
            venue_data['name'] = venue.name
            venue_data['num_upcoming_shows'] = len(
                [1 for show in venue.shows if show.start_time > datetime.now()])
            # Add this venue data to the city_data['venues']
            city_data['venues'].append(venue_data)

        # Add this city_data to the overall data
        data.append(city_data)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    venues = db.session.query(Venue).filter(Venue.name.ilike(
        '%'+request.form.get('search_term', '')+'%')).all()

    response = {
        "count": len(venues),
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    data = {}

    data['id'] = venue.id
    data['name'] = venue.name
    data['genres'] = venue.genres
    data['city'] = venue.city
    data['state'] = venue.state
    data['phone'] = venue.phone
    data['website'] = venue.website
    data['facebook_link'] = venue.facebook_link
    data['seeking_description'] = venue.seeking_description
    data['image_link'] = venue.image_link
    data['upcoming_shows'] = [
        {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'start_time': show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        } for show in venue.shows if show.start_time > datetime.now()
    ]
    data['upcoming_shows_count'] = len(data['upcoming_shows'])

    data['past_shows'] = [
        {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'start_time': show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        } for show in venue.shows if show.start_time < datetime.now()
    ]
    data['past_shows_count'] = len(data['past_shows'])

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    if form.validate():

        # TODO: insert form data as a new Venue record in the db, instead
        venue = Venue(
            name=request.form.get('name'),
            state=request.form.get('state'),
            city=request.form.get('city'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            genres=request.form.getlist('genres'),
            facebook_link=request.form.get('facebook_link')
        )
        db.session.add(venue)
        db.session.commit()

        # TODO: modify data to be the data object returned from db insertion

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        return render_template('pages/show_venue.html', venue=venue)
    else:
        return render_template('forms/new_venue.html', form=form)


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = Venue.query.get(venue_id)
    try:
        db.session.delete(venue)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
    finally:
        db.session.close()
    return jsonify({'success': True})

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    artists = db.session.query(Artist).filter(Artist.name.ilike(
        '%'+request.form.get('search_term', '')+'%')).all()

    response = {
        "count": len(artists),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    artist = Artist.query.get(artist_id)
    data = {}

    data['id'] = artist.id
    data['name'] = artist.name
    data['genres'] = artist.genres
    data['city'] = artist.city
    data['state'] = artist.state
    data['phone'] = artist.phone
    data['website'] = artist.website
    data['facebook_link'] = artist.facebook_link
    data['seeking_venue'] = artist.seeking_venue
    data['seeking_description'] = artist.seeking_description
    data['image_link'] = artist.image_link
    data['upcoming_shows'] = [
        {
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'start_time': show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        } for show in artist.shows if show.start_time > datetime.now()
    ]
    data['upcoming_shows_count'] = len(data['upcoming_shows'])

    data['past_shows'] = [
        {
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'start_time': show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        } for show in artist.shows if show.start_time < datetime.now()
    ]
    data['past_shows_count'] = len(data['past_shows'])

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    e_artist = db.session.query(Artist).filter_by(id=artist_id).one()
    e_artist.name = request.form.get('name')
    e_artist.state = request.form.get('state')
    e_artist.city = request.form.get('city')
    e_artist.phone = request.form.get('phone')
    e_artist.genres = request.form.getlist('genres')
    e_artist.facebook_link = request.form.get('facebook_link')

    db.session.commit()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    e_venue = db.session.query(Artist).filter_by(id=artist_id).one()
    e_venue.name = request.form.get('name')
    e_venue.state = request.form.get('state')
    e_venue.city = request.form.get('city')
    e_venue.phone = request.form.get('phone')
    e_venue.genres = request.form.getlist('genres')
    e_venue.facebook_link = request.form.get('facebook_link')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    form = ArtistForm(request.form)
    if form.validate():
        artist = Artist(
            name=request.form.get('name'),
            state=request.form.get('state'),
            city=request.form.get('city'),
            phone=request.form.get('phone'),
            genres=request.form.getlist('genres'),
            website=request.form.get('website'),
            facebook_link=request.form.get('facebook_link')
        )
        try:
            db.session.add(artist)
            db.session.commit()
            flash('Artist was successfully listed!')
            return redirect(url_for('show_artist', artist_id=artist.id))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('An error occurred. Artist could not be listed.')
        
    return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    data = []

    shows = Show.query.all()
    data = [
        {
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        } for show in shows
    ]

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    form = ShowForm(request.form)
    if form.validate():

        # TODO: insert form data as a new Venue record in the db, instead
        show = Show(
            artist_id=request.form.get('artist_id'),
            venue_id=request.form.get('venue_id'),
            start_time=request.form.get('start_time')
        )
        try:
            db.session.add(show)
            db.session.commit()
            flash('Show was successfully listed!')
            return render_template('pages/show.html', show=show)
        except Exception as e:
            print("error")
            print(e)
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
            return render_template('forms/new_show.html', form=form)

        # TODO: modify data to be the data object returned from db insertion

        # on successful db insert, flash success
        
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        
    else:
        flash('An error occurred. Show could not be listed.')
        return render_template('forms/new_show.html', form=form)


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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
