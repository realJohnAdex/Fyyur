#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

from sqlalchemy.exc import SQLAlchemyError
from models import db_setup, Venue, Show, Artist
from sqlalchemy.dialects.postgresql import ARRAY
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
# to setup the database connection to a local postgresql database
app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)
db.create_all()
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  # formatting to accept Parser as datetime and string or character stream
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value

  if format == 'full':
    format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
    format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Functionss.
#----------------------------------------------------------------------------#
current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')

def get_object_attributes(obj):
  return vars(obj)
  
def artist_details(Show):
  return{
    'artist_id' :Show.artist_id,
    'artist_name' :Show.Artists.name,
    'artist_image_link' :Show.Artists.image_link,
    'start_time' :Show.start_time
    }

def venue_details(Show):
  return{
    'venue_id' :Show.venue_id,
    'venue_name' :Show.Venues.name,
    'venue_image_link' :Show.Venues.image_link,
    'start_time' :Show.start_time
    }

def show_details(show):
  return{
    'venue_id' :show.venue_id,
    'venue_name' :show.Venues.name,
    'artist_id' :show.artist_id,
    'artist_name' :show.Artists.name,
    'artist_image_link' :show.Artists.image_link,
    'start_time' :show.start_time
    }

def get_upcoming_shows(query_item):
  return query_item.shows.filter(Show.start_time > current_time).all()

def filter_upcoming_shows(shows):
  return shows.filter(Show.start_time > current_time).all()
  return upcoming_shows

def filter_past_shows(shows):
  return shows.filter(Show.start_time <= current_time).all()
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
  # num_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.order_by(Venue.id, Venue.state, Venue.city).all()
  data = []
  data_item = {}
  position = 0
  for venue in venues:
    data_item = {
        "city": venue.city,
        "state": venue.state,
        "venues": [{
          "id": venue.id,
          "name":venue.name,
          "num_upcoming_shows": len(get_upcoming_shows(venue))}]
        }
    if not data:
      data.append(data_item)
    else:
      # search "data" to find the index of item with same city and state
      for i, dic in enumerate(data):
        if dic['city'] == venue.city and dic['state'] == venue.state:
          position = i
          data[position]["venues"].append(data_item.get("venues")[0])
          break
      else:
        data.append(data_item)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  venue_query = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).order_by('name').all()
  venue_data = [{
    "id": venue.id,
    "name": venue.name,
    "num_upcoming_shows": len(get_upcoming_shows(venue))
  } for venue in venue_query]
  response = {
    "count":len(venue_data),
    "data": venue_data,
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue_query = Venue.query.get(venue_id)
  if venue_query:
    venue_details = get_object_attributes(venue_query)
    #show_query, returns all shows for the given venue
    shows_query = Show.query.options(db.joinedload(Show.Venues)).filter(Show.venue_id == venue_id)
    upcoming_shows = filter_upcoming_shows(shows_query)
    upcoming_shows_artists = list(map(artist_details, upcoming_shows))
    venue_details["upcoming_shows"] = upcoming_shows_artists
    venue_details["upcoming_shows_count"] = len(upcoming_shows)
    past_shows = filter_past_shows(shows_query)
    past_shows_artists = list(map(artist_details, past_shows))
    venue_details["past_shows"] = past_shows_artists
    venue_details["past_shows_count"] = len(past_shows)

    return render_template('pages/show_venue.html', venue=venue_details)
  else:
    return render_template('errors/404.html')

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    seeking_talent = False
    if 'seeking_talent' in request.form:
      seeking_talent = request.form['seeking_talent'] == 'y'
    new_venue = Venue(
      name=request.form['name'],
      genres=request.form.getlist('genres'),
      address=request.form['address'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      website_link=request.form['website_link'],
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link'],
      seeking_talent=seeking_talent,
      seeking_description=request.form['seeking_description'],
    )
    #insert new venue records into the db
    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue: ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except SQLAlchemyError as e:
    flash('An error occurred. Venue: ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
    error = True
    error_msg = str(e)
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  venue = Venue.query.get(venue_id)
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue: ' + venue.name + ' with ID: ' + venue_id + ' was successfully deleted')
  except SQLAlchemyError as e:
    error = True
    db.session.rollback()
    flash('Error occurred!, Venue: ' + venue.name + ' with ID: ' + venue_id + ' was not deleted') 
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.order_by('name').all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  artist_query = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).order_by('name').all()
  artist_data = [{
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(get_upcoming_shows(artist))
  } for artist in artist_query]
  response = {
    "count":len(artist_data),
    "data": artist_data,
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist_query = Artist.query.get(artist_id)
  if artist_query:
    artist_details = get_object_attributes(artist_query)
    #show_query, returns all shows for the given artist
    shows_query = Show.query.options(db.joinedload(Show.Artists)).filter(Show.artist_id == artist_id)
    upcoming_shows = filter_upcoming_shows(shows_query)
    upcoming_shows_venues = list(map(venue_details, upcoming_shows))
    artist_details["upcoming_shows"] = upcoming_shows_venues
    artist_details["upcoming_shows_count"] = len(upcoming_shows)
    past_shows = filter_past_shows(shows_query)
    past_shows_venues = list(map(venue_details, past_shows))
    artist_details["past_shows"] = past_shows_venues
    artist_details["past_shows_count"] = len(past_shows)

    return render_template('pages/show_artist.html', artist=artist_details)
  else:
    return render_template('errors/404.html')

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if artist:
    artist_details = get_object_attributes(artist)
    form.name.data = artist_details["name"]
    form.city.data = artist_details["city"]
    form.state.data = artist_details["state"]
    form.phone.data = artist_details["phone"]
    form.genres.data = artist_details["genres"]
    form.facebook_link.data = artist_details["facebook_link"]
    form.website_link.data = artist_details["website_link"]
    form.image_link.data = artist_details["image_link"]
    form.seeking_venue.data = artist_details["seeking_venue"]
    form.seeking_description.data = artist_details["seeking_description"]
    return render_template('forms/edit_artist.html', form=form, artist=artist_details)
  else:
    return render_template('errors/404.html')
  # TODO: populate form with fields from artist with ID <artist_id>
  
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  try:
    artist = Artist.query.get(artist_id)
    if not (artist):
      return render_template('errors/404.html')
    if form.validate():
      seeking_venue = request.form[
          'seeking_venue'] == 'y' if 'seeking_venue' in request.form else False
      setattr(artist, 'name', request.form['name'])
      setattr(artist, 'city', request.form['city'])
      setattr(artist, 'state', request.form['state'])
      setattr(artist, 'phone', request.form['phone'])
      setattr(artist, 'genres', request.form.getlist('genres'))
      setattr(artist, 'facebook_link', request.form['facebook_link'])
      setattr(artist, 'image_link', request.form['image_link'])
      setattr(artist, 'website_link', request.form['website_link'])
      setattr(artist, 'seeking_venue', seeking_venue)
      setattr(artist, 'seeking_description', request.form['seeking_description'])
      db.session.commit()
      flash('Artist: ' + request.form['name'] + ' was successfully updated!')
  except SQLAlchemyError as e:
    db.session.rollback()
    flash('An error occurred. Artist: ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if venue:
    venue_details = get_object_attributes(venue)
    form.name.data = venue_details["name"]
    form.city.data = venue_details["city"]
    form.state.data = venue_details["state"]
    form.address.data = venue_details["address"]
    form.phone.data = venue_details["phone"]
    form.genres.data = venue_details["genres"]
    form.facebook_link.data = venue_details["facebook_link"]
    form.image_link.data = venue_details["image_link"]
    form.website_link.data = venue_details["website_link"]
    form.seeking_talent.data = venue_details["seeking_talent"]
    form.seeking_description.data = venue_details["seeking_description"]
    return render_template('forms/edit_venue.html', form=form, venue=venue_details)
  else:
    return render_template('errors/404.html')
  # TODO: populate form with values from venue with ID <venue_id>

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  try:
    venue = Venue.query.get(venue_id)
    if venue:
      if form.validate():
        seeking_talent = False
        if 'seeking_talent' in request.form:
          seeking_talent = request.form['seeking_talent'] == 'y'
        setattr(venue, 'name', request.form['name'])
        setattr(venue, 'city', request.form['city'])
        setattr(venue, 'state', request.form['state'])
        setattr(venue, 'address', request.form['address'])
        setattr(venue, 'phone', request.form['phone'])
        setattr(venue, 'genres', request.form.getlist('genres'))
        setattr(venue, 'facebook_link', request.form['facebook_link'])
        setattr(venue, 'image_link', request.form['image_link'])
        setattr(venue, 'website_link', request.form['website_link'])
        setattr(venue, 'seeking_talent', seeking_talent)
        setattr(venue, 'seeking_description', request.form['seeking_description'])
        db.session.commit()
        flash('Venue: ' + request.form['name'] + ' was successfully updated!')
    else:
      return render_template('errors/404.html')
  except SQLAlchemyError as e:
    db.session.rollback()
    flash('An error occurred. Venue: ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
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
  # TODO: modify data to be the data object returned from db insertion
  try:
    seeking_venue = False
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
    new_artist = Artist(
      name=request.form['name'],
      city=request.form['city'],
      state= request.form['state'],
      phone=request.form['phone'],
      genres=request.form.getlist('genres'),
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link'],
      website_link=request.form['website_link'],
      seeking_venue=seeking_venue,
      seeking_description=request.form['seeking_description'],
    )
    #insert new artist records into the db
    db.session.add(new_artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist: ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except SQLAlchemyError as e:
    flash('An error occurred. Artist: ' + request.form['name'] + 'could not be listed.')
    db.session.rollback()
    error = True
    error_msg = str(e)
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #a query of all shows from db using join
  show_query = Show.query.options(db.joinedload(Show.Venues), db.joinedload(Show.Artists)).order_by('start_time').all()
  data = list(map(show_details, show_query))
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
  error = False
  try:
    new_show = Show(
      venue_id=request.form['venue_id'],
      artist_id=request.form['artist_id'],
      start_time=request.form['start_time'],
    )
    db.session.add(new_show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except SQLAlchemyError as e:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occured. Show could not be listed.')
    db.session.rollback()
    error = True
    error_msg = str(e)
  finally:
    db.session.close()
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
