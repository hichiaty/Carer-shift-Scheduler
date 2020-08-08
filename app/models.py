from flask_sqlalchemy import SQLAlchemy
from app import app
from app import db

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