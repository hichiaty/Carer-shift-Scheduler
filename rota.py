from flask import Flask, render_template, url_for, request, redirect, Response, abort, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_mail import Mail, Message
import os
import calendar
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app/rota.db'
app.secret_key = 'super secret keylol'
app.debug=True
db = SQLAlchemy(app)

daynames = ['Sunday','Monday','Tuesday','Wednesday', 'Thursday', 'Friday', 'Saturday']*5
bidding = True

class Shift(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    shift_type = db.Column(db.Integer, nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    covered = db.Column(db.Integer, default=0)
    covered_by = db.Column(db.Integer, db.ForeignKey('team.id'))

    def __repr__(self):
        return '<Shift %r>' % self.id

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    psswd = db.Column(db.String(120), nullable=False)
    shifts = db.relationship('Shift', backref='shifts', lazy=True)
    num_shifts_covered = db.Column(db.Integer, default=0)
    role = db.Column(db.Integer, nullable=False)
    photo = db.Column(db.String(120))
    
    def __repr__(self):
        return '<User %r>' % self.name
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Unavailabilities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    which_day =  db.Column(db.Integer, nullable=False)
    day_or_night = db.Column(db.Integer, nullable=False, default=0) #0=day,1=night
    person_unavailable = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    
    def __repr__(self):
        return '<Unavailability %r>' % self.id

class Swaps(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_id1 =  db.Column(db.Integer, nullable=False)
    shift_id2 =  db.Column(db.Integer, nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    decision_maker_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    fullfilment_status = db.Column(db.Boolean, nullable=False, default=False)
    reason = db.Column(db.String(250), nullable=False)
    rejected = db.Column(db.Boolean, nullable=False, default=False)

    
    def __repr__(self):
        return '<Swap %r>' % self.id

class Bids(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    
    def __repr__(self):
        return '<Bid %r>' % self.id

def generate_monthly_database():
    #get num of days in month
    now = datetime.datetime.now()
    daysinmonth = calendar.monthrange(now.year, now.month)[1]

    db.create_all()
    for i in range(1,daysinmonth+1):
        new_shift_day=Shift(shift_type=0, shift_date=date(now.year,now.month,i), covered=0, covered_by=None)
        new_shift_night1=Shift(shift_type=1, shift_date=date(now.year,now.month,i), covered=0, covered_by=None)
        new_shift_night2=Shift(shift_type=1, shift_date=date(now.year,now.month,i), covered=0, covered_by=None)
                
        db.session.add(new_shift_day)
        db.session.add(new_shift_night1)
        db.session.add(new_shift_night2)
        db.session.commit()

                
    for x in range(1,11):
        newteam=Team(name='name', psswd='Password{}'.format(x), shifts=[], num_shifts_covered=0, role=1)
        db.session.add(newteam)
        db.session.commit()

if __name__ == '__main__':
    generate_monthly_database()


# def autoassign():
#     shifts = Shift.query.order_by(Shift.id).all()
#     for shift in shifts:
#         bids_for_shift = Bids.query.filter_by(shift_id=shift.id).all()
#         if len(bids_for_shift) == 1:
#             #assign shift to bidder
#             assignshift(shift,bids_for_shift[0])
#         else: 
#             for bid in bids_for_shift:
#                 #

# def assignshift(shift, bid):
#     if shift.covered==0:
#         shift.covered=1
#         shift.covered_by = bid.bidder_id
#     else: 
#         print('something so bad is happening')
#     try:
#         db.session.commit()
#         print('change happened')
#     except:
#         print('There was an issue updating the shift')
