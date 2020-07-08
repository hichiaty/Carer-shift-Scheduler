from flask import Flask, render_template, url_for, request, redirect, Response, abort, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_mail import Mail, Message
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rota.db'
app.secret_key = 'super secret keylol'
app.debug=True

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": os.environ["MAIL_USERNAME"],
    "MAIL_PASSWORD": os.environ["MAIL_PASSWORD"]
}

app.config.update(mail_settings)
mail = Mail(app)



login_manager = LoginManager()
login_manager.init_app(app)


db = SQLAlchemy(app)

daynames = ['Sunday','Monday','Tuesday','Wednesday', 'Thursday', 'Friday', 'Saturday']*5
bidding = False

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

    # def __init__(self):
    #     self.id = id
    #     self.name = name
    #     self.psswd = psswd
    #     self.shifts = shifts
    #     self.num_shifts_covered = num_shifts_covered
    #     self.role = role



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

    # _unavailability =db.Column(db.String, default='0.0')

    # @property
    # def unavailability(self):
    #     return [int(x) for x in self._unavailability.split(';')]
    # @unavailability.setter
    # def unavailability(self, value):
    #     try:
    #         int(value)
    #         self._unavailability += ';%s' % value 
    #     except:
    #         print('uh oh, can\'t int value')





    




def generate_init_database():
    db.create_all()
    for i in range(1,31):
        new_shift_day=Shift(shift_type=0, shift_date=date(2019,9,i), covered=0, covered_by=None)
        new_shift_night1=Shift(shift_type=1, shift_date=date(2019,9,i), covered=0, covered_by=None)
        new_shift_night2=Shift(shift_type=1, shift_date=date(2019,9,i), covered=0, covered_by=None)
                
        db.session.add(new_shift_day)
        db.session.add(new_shift_night1)
        db.session.add(new_shift_night2)
        db.session.commit()

                
    for x in range(1,11):
        newteam=Team(name='name', psswd='Password{}'.format(x), shifts=[], num_shifts_covered=0, role=1)
        db.session.add(newteam)
        db.session.commit()












# Routing begins here
#login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        user_id = request.form['userid']
        password = request.form['password']        
        if password == 'password':
            user = Team.query.get_or_404(user_id)
            login_user(user, remember=True)
            if current_user.role==0:
                return redirect('/admin-rota')
            elif bidding==True:
                return redirect('/bidding')
            else:
                return redirect('/rota')
        else:
            return abort(401)
    else:
        team = Team.query.order_by(Team.id).all()
        return render_template('login.html', team=team)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/') 

# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return redirect('/')  

# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return Team.query.get_or_404(userid)


@app.route('/static/staffimgs/<path:filename>')
@login_required
def staffimgsroute(filename):
    if filename[:-4] != current_user.photo:
        return redirect('/rota')
    else:
        return send_from_directory('static/staffimgs',filename)

@app.route('/rota',methods=['POST','GET'])
@login_required
def rota():
    if bidding == True:
        return redirect('/bidding')
    if request.method == 'POST':
        #ADD SHIFT?
        pass
    else:
        shifts = Shift.query.order_by(Shift.shift_date).all()
        # print(shifts)
        days = [shifts[3*i:3*(i+1)] for i in range(int(len(shifts)/3))]   
        # print(days) 
        unavdays = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=0 ).all()
        unavnights = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=1 ).all()
        img = url_for('static', filename='staffimgs/{}.png'.format(Team.query.get_or_404(current_user.id).photo))
        swaps = Swaps.query.filter((Swaps.requester_id==current_user.id) | (Swaps.decision_maker_id==current_user.id)).all()
        shiftids = shifts = Shift.query.order_by(Shift.id).all()
        return render_template('rota.html', shiftids=shiftids, days=days, daynames=daynames, unavnights=unavnights, unavdays=unavdays, img=img, swaps=swaps)


@app.route('/admin-rota',methods=['POST','GET'])
@login_required
def adminrota():
    if current_user.role==0:
        if request.method=='POST':
            shift_id = request.form['shiftid']
            carer_id = request.form['userid']
            shift = Shift.query.get_or_404(shift_id)
            if shift.covered == 0:  
                shift.covered=1
                shift.covered_by = carer_id
            else:
                shift.covered=0
                shift.covered_by = None
            try:
                db.session.commit()
                print('change happened')
                return redirect('/admin-rota')
            except:
                print('There was an issue updating your shift')
                return redirect('/admin-rota')
        else: #get
            shifts = Shift.query.order_by(Shift.shift_date).all()
            for shift in shifts:
                if shift.covered !=0:
                    shift.covered_by_name = Team.query.filter_by(id=shift.covered_by).first().name
            days = [shifts[3*i:3*(i+1)] for i in range(int(len(shifts)/3))]
            team = Team.query.filter_by(role=1).all()
            return render_template('admin-rota.html', days=days, daynames=daynames, team=team)
    else:
        return redirect('/rota')

@app.route('/updateshift/<int:id>')
@login_required
def update(id):
    if bidding == True:
        return redirect('/bidding')
    shift = Shift.query.get_or_404(id)
    #CHECK IF IT'S POSSIBLE BASED ON PREVIOUS SHIFTS
    if shift.covered==0:
        shift.covered=1
        shift.covered_by = current_user.id
    elif shift.covered_by is not None and shift.covered_by == current_user.id and bidding!=True:
            shift.covered=0
            shift.covered_by=None
    else: 
        return Response('YOU DO NOT HAVE PERMISSION TO CHANGE THIS SHIFT')
    try:
        db.session.commit()
        print('change happened')
        return redirect('/rota')
    except:
        print('There was an issue updating your shift')
        return redirect('/rota')

@app.route('/swapshift', methods=['POST','GET'])
@login_required
def swap():
    if bidding == True:
        return redirect('/bidding')
    if request.method=='POST':
        id1 = int(request.form['id1'])
        id2 = int(request.form['id2'])
        print(id1,id2)
        shift1 = Shift.query.get_or_404(id1)
        shift2 = Shift.query.get_or_404(id2)
        requester = int(shift1.covered_by)
        print('requester',requester)
        decision_maker = int(shift2.covered_by)
        #check if swaps for same shifts and users already exist
        all_swaps = Swaps.query.filter_by(requester_id=requester, decision_maker_id=decision_maker, shift_id1=shift1.id, shift_id2=shift2.id, fullfilment_status = False).all()
        if len(all_swaps)==1 and current_user.id!=decision_maker:
            return redirect('/rota')
        if decision_maker == current_user.id:
            accept = True if request.form['accept'] == 'true' else False
            #accept swap update shift
            curr_swap = Swaps.query.filter_by(requester_id=requester, decision_maker_id=decision_maker, fullfilment_status=False).first()
            if accept:
                shift1.covered_by = decision_maker
                shift2.covered_by = requester
                curr_swap.fullfilment_status = True
                # with app.app_context():
                #     msg = Message(subject="Hello",
                #       sender=app.config.get("MAIL_USERNAME"),
                #       recipients=["hichiaty@gmail.com"], # use your email for testing
                #       body="Shift accepted bro")
                #     mail.send(msg)
            # if a shift has been accepted, remove all other requests for that shift
                db.session.commit()
                swaps_remain = Swaps.query.filter_by(requester_id=requester, shift_id1=shift1.id, fullfilment_status = False).all()
                for u in swaps_remain:
                    db.session.delete(u)
                db.session.commit()    
            else:
                #reject
                curr_swap.rejected=True
                curr_swap.fullfilment_status = True
            try:
                db.session.commit() 
                print('change happened')
                return redirect('/rota')
            except:
                print('There was an issue updating your shift')
                return redirect('/rota')
        else:
            #create a swap request
            reason = request.form['reason']
            swap = Swaps(shift_id1=shift1.id, shift_id2=shift2.id,
                    requester_id=requester, decision_maker_id=decision_maker,
                    fullfilment_status=False, reason=reason, rejected=False)
            try:
                db.session.add(swap)
                db.session.commit()
                print('change happened')
                return redirect('/rota')
            except:
                print('There was an issue updating your shift')
                return redirect('/rota')
    else:
        return redirect('/rota')

@app.route('/updateavailability', methods=['POST','GET'])
@login_required
def unavailability():
    if request.method=='POST':
        daylist = request.form['dateday']
        nightlist = request.form['datenight']
        current_unavail = Unavailabilities.query.filter_by(person_unavailable=current_user.id).all()
        for i in current_unavail:
            db.session.delete(i)
        try:
            daylist = [int(i) for i in daylist.strip('[').strip(']').split(',')]
        except ValueError:
            daylist=[]
        try:    
            nightlist = [int(i) for i in nightlist.strip('[').strip(']').split(',')]
        except ValueError:
            nightlist=[]
        for day in daylist:
            unav = Unavailabilities(day_or_night=0, person_unavailable=current_user.id, which_day =  day)
            db.session.add(unav)
        for night in nightlist:
            unav = Unavailabilities(day_or_night=1, person_unavailable=current_user.id, which_day =  night)
            db.session.add(unav)
        try:
            db.session.commit()
            print('change happened')
            return redirect('/rota')
        except:
            print('There was an issue updating your unavailability')
            return redirect('/rota') 
    else: #get
        return redirect('/rota')  


@app.route('/bidding', methods=['POST','GET'])
@login_required
def bidding_func():
    if request.method == 'POST':
        #if bid exists remove it
        bidder_id = current_user.id
        shift_id = int(request.form['shiftid'])
        current_bids = Bids.query.filter_by(shift_id=shift_id, bidder_id=bidder_id).all()
        if len(current_bids) != 0:
            for bid in current_bids:
                db.session.delete(bid)
            try:
                db.session.commit()
                print('change happened')
                return redirect('/bidding')
            except:
                print('There was an issue updating your shift')
                return redirect('/bidding')
        else:
            bid = Bids(shift_id=shift_id, bidder_id=bidder_id)
            try:
                db.session.add(bid)
                db.session.commit()
                print('change happened')
                return redirect('/bidding')
            except:
                print('There was an issue updating your shift')
                return redirect('/bidding')
    else:
        shifts = Shift.query.order_by(Shift.shift_date).all()
        days = [shifts[3*i:3*(i+1)] for i in range(int(len(shifts)/3))]    
        unavdays = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=0 ).all()
        unavnights = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=1 ).all()
        img = url_for('static', filename='staffimgs/{}.png'.format(Team.query.get_or_404(current_user.id).photo))
        shiftids = shifts = Shift.query.order_by(Shift.id).all()
        bids = Bids.query.filter_by(bidder_id=current_user.id).all()
        return render_template('biddingrota.html', shiftids=shiftids, days=days, daynames=daynames, unavnights=unavnights, unavdays=unavdays, img=img, bids=bids)


if __name__ == '__main__':
    app.run(host= '0.0.0.0')
    #generate_init_database()


def autoassign():
    shifts = Shift.query.order_by(Shift.id).all()
    for shift in shifts:
        bids_for_shift = Bids.query.filter_by(shift_id=shift.id).all()
        if len(bids_for_shift) == 1:
            #assign shift to bidder
            assignshift(shift,bids_for_shift[0])
        else: 
            for bid in bids_for_shift:
                #

def assignshift(shift, bid):
    if shift.covered==0:
        shift.covered=1
        shift.covered_by = bid.bidder_id
    else: 
        print('something so bad is happening')
    try:
        db.session.commit()
        print('change happened')
    except:
        print('There was an issue updating the shift')
