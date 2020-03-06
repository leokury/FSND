#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import ARRAY, String
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://leokury@localhost:5432/fyyur'


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
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(ARRAY(String))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def serialize(self):
      return { 
        "id": self.id,
        "name": self.name,
        "city": self.city,
        "state": self.state,
        "address": self.address,
        "phone": self.phone,
        "image_link": self.image_link,
        "facebook_link": self.facebook_link,
        "genres": self.genres
      }

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def serialize(self):
      return { 
        "id": self.id,
        "name": self.name,
        "city": self.city,
        "state": self.state,
        "phone": self.phone,
        "image_link": self.image_link,
        "facebook_link": self.facebook_link,
        "genres": self.genres,
      }

class Show(db.Model):

    __tablename__ = 'Show'
    id = db.Column(db.Integer,primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id), nullable=False)
    start_time = db.Column(db.String(), nullable=False)

    def serialize(self):
      return { 
        "id": self.id,
        "venue_id": self.venue_id,
        "artist_id": self.artist_id,
        "start_time": self.start_time
      }

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
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
  data = Venue.query.all()
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  venue_list = Venue.query.filter(Venue.name.ilike('%' + request.form['search_term'] + '%')).all()
  response={
    "count": len(venue_list),
    "data": []
  }
  for venue in venue_list:
    response["data"].append(venue)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  data = Venue.query.get(venue_id).serialize()
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  # append shows to this venue
  new_shows = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time >= current_time).all()
  data["upcoming_shows"] = [show.serialize() for show in new_shows]
  data["upcoming_shows_count"] = len(new_shows)
  past_shows = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time < current_time).all()
  data["past_shows_count"] = len(past_shows)
  data["past_shows"] = [show.serialize() for show in past_shows]

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
    venue = Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres')

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully listed!')
  except:
    error = True
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  
  if not error:
    return render_template('pages/home.html')
  else:
    abort(500)
 

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.get(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback() 
  finally:
    db.session.close()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  artist_list = Artist.query.filter(Artist.name.ilike('%' + request.form['search_term'] + '%')).all()
  response={
    "count": len(artist_list),
    "data": []
  }
  for artist in artist_list:
    response["data"].append(artist)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = Artist.query.get(artist_id).serialize()

  # append past and upcoming shows
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  new_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time >= current_time).all()
  data["upcoming_shows"] = [show.serialize() for show in new_shows]
  data["upcoming_shows_count"] = len(new_shows)
  past_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time < current_time).all()
  data["past_shows_count"] = len(past_shows)
  data["past_shows"] = [show.serialize() for show in past_shows]

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
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
    #populating artist
    artist = Artist()

    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']
    artist.genres = request.form['genres']

    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully listed!')
  except:
    error = True
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  
  if not error:
    return render_template('pages/home.html')
  else:
    abort(500)

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = Show.query.all()
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
    #populating new show
    show = Show()
    show.venue_id = request.form['venue_id']
    show.artist_id = request.form['artist_id']
    show.start_time = request.form['start_time']
    
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    flash('An error occurred. Show could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  
  if not error:
    return render_template('pages/home.html')
  else:
    abort(500)
  
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
