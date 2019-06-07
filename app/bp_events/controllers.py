from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
#from app.bp_events.forms import CreateEvent
from app import app


events = Blueprint('events', __name__, template_folder='templates')

#@events.route('/')
#def events_home():
#	return "events homepage"

#@events.route('/')
#def events_home():
#	return render_template('events/list.html')

#@events.route('/')
#def events_home():
#	return render_template('events/date.html', myname="anyu")
	#return render_template('events/listv2.html', myname="anyu")

@events.route('/')
def events_home():
	return render_template('events/listv3.html', myname="anyu")
	

@events.route('/create')
@login_required
def events_create():
	form = CreateEvent()
	return render_template('events/create.html', form=form)
