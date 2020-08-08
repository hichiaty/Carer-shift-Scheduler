from flask import Flask, render_template, url_for, request, redirect, Response, abort, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_mail import Mail, Message
import os
from app.models import *
from app import app, login_manager, mail
import calendar
import datetime
from sqlalchemy import extract


bidding = False
daynames = ['Sunday','Monday','Tuesday','Wednesday', 'Thursday', 'Friday', 'Saturday']*5
now = datetime.datetime.now()
rota_name = now.strftime('%B %Y')



# index or login
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
        return render_template('login.html', now=now, team=team, rota_name=rota_name)

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
        shifts = Shift.query.order_by(Shift.shift_date).filter(extract('month', Shift.shift_date) == now.month).all()
        # print(shifts)
        days = [shifts[3*i:3*(i+1)] for i in range(int(len(shifts)/3))]
        # print(days) 
        unavdays = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=0 ).all()
        unavnights = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=1 ).all()
        img = url_for('static', filename='staffimgs/{}.png'.format(Team.query.get_or_404(current_user.id).photo))
        swaps = Swaps.query.filter((Swaps.requester_id==current_user.id) | (Swaps.decision_maker_id==current_user.id)).all()
        shiftids = shifts = Shift.query.order_by(Shift.id).filter(extract('month', Shift.shift_date) == now.month).all()
        return render_template('rota.html', now=now, rota_name=rota_name, shiftids=shiftids, days=days, daynames=daynames, unavnights=unavnights, unavdays=unavdays, img=img, swaps=swaps)


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
            shifts = Shift.query.order_by(Shift.shift_date).filter(extract('month', Shift.shift_date) == now.month).all()
            for shift in shifts:
                if shift.covered !=0:
                    shift.covered_by_name = Team.query.filter_by(id=shift.covered_by).first().name
            days = [shifts[3*i:3*(i+1)] for i in range(int(len(shifts)/3))]
            team = Team.query.filter_by(role=1).all()
            return render_template('admin-rota.html', now=now, days=days, daynames=daynames, team=team,  rota_name=rota_name)
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
        # if already bidded (is that the past tense of bid?), then remove bid
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
        shifts = Shift.query.order_by(Shift.shift_date).filter(extract('month', Shift.shift_date) == now.month).all()
        days = [shifts[3*i:3*(i+1)] for i in range(int(len(shifts)/3))]    
        unavdays = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=0 ).all()
        unavnights = Unavailabilities.query.filter_by(person_unavailable=current_user.id, day_or_night=1 ).all()
        img = url_for('static', filename='staffimgs/{}.png'.format(Team.query.get_or_404(current_user.id).photo))
        shiftids = shifts = Shift.query.order_by(Shift.id).filter(extract('month', Shift.shift_date) == now.month).all()
        bids = Bids.query.filter_by(bidder_id=current_user.id).all()
        return render_template('biddingrota.html', now=now, rota_name=rota_name, shiftids=shiftids, days=days, daynames=daynames, unavnights=unavnights, unavdays=unavdays, img=img, bids=bids)
