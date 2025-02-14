from datetime import datetime, date, timedelta
from . import db
from .models import User, Pointstable, Fixture, Squad
import os, csv, re, pytz
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import login_required, current_user
from sqlalchemy import and_, or_
from sqlalchemy.sql import text

main = Blueprint('main', __name__)

tz = pytz.timezone('Asia/Kolkata')

pofs = {'E':'Eliminator', 'F':'Final'}

liveURL_Prefix = "https://cmc2.sportskeeda.com/live-cricket-score/"
liveURL_Suffix = "/ajax"

full_name = {'DCW':'Delhi Capitals',
             'GG':'Gujarat Giants',
             'MIW':'Mumbai Indians',
             'RCBW':'Royal Challengers Bengaluru',
             'UPW':'UP Worriorz',
             'TBA':'TBA'}

liveTN = {'DCW':'Delhi Capitals Women',
          'GG':'Gujarat Giants Women',
          'MIW':'Mumbai Indians Women',
          'RCBW':'Royal Challengers Bengaluru Women',
          'UPW':'UP Worriorz'}

clr = {'DCW':{'c1':'#d71921', 'c2':'#2561ae', 'c3':'#282968'},
        'GG':{'c1':'#ffe338', 'c2':'#e27602', 'c3':'#ff6600'},
        'MIW':{'c1':'#004ba0', 'c2':'#0077b6', 'c3':'#d1ab3e'},
        'RCBW':{'c1':'#2b2a29', 'c2':'#444444', 'c3':'#ec1c24'},
        'UPW': {'c1': '#7600bc', 'c2': '#b100cd', 'c3': '#ffff00'}}

ptclr = {'DCW':{'c1':'#024c8d', 'c2':'#04046c', 'c3':'#e00034'},
        'GG':{'c1':'#fba146', 'c2':'#e0590b', 'c3':'#f3bc44'},
        'MIW':{'c1':'#0077b6', 'c2':'#004ba0', 'c3':'#aa9174'},
        'RCBW':{'c1':'#e40719', 'c2':'#7e2a20', 'c3':'#2b2a29'},
        'UPW': {'c1': '#6e30bb', 'c2': '#3c0070', 'c3':'#ed5089'}}

def oversAdd(a, b):
    A, B = round(int(a)*6 + (a-int(a))*10, 0), round(int(b)*6 + (b-int(b))*10, 2)
    S = int(A) + int(B)
    s = S//6 + (S%6)/10
    return s

def oversSub(a, b):
    A, B = round(int(a) * 6 + (a - int(a)) * 10, 0), round(int(b) * 6 + (b - int(b)) * 10, 2)
    S = int(A) - int(B)
    s = S // 6 + (S % 6) / 10
    return s

def ovToPer(n):
    return (int(n)+((n-int(n))*10)/6)


@main.route('/')
def index():
    if db.session.execute(text('select count(*) from user')).scalar() == 0:
        user = User(email='adminwpl2025@gmail.com', \
                    password=generate_password_hash('Admin@wpl2025', method='pbkdf2:sha256', salt_length=8), \
                    name='AdminWPL2025')
        db.session.add(user)
        db.session.commit()
    if db.session.execute(text('select count(*) from pointstable')).scalar() == 0:
        teams = ['DCW', 'GG', 'MIW', 'RCBW', 'UPW']
        inter = os.getcwd()
        for i in teams:
            tm = Pointstable(team_name=i, P=0,W=0,L=0,NR=0,\
                    Points=0, NRR=0.0, Win_List=str({}),\
                logo_path='{}/WPL/static/images/{}.png'.format(inter,i),\
                For={'runs':0, 'overs':0.0}, Against={'runs':0, 'overs':0.0})
            db.session.add(tm)
            db.session.commit()
    if db.session.execute(text('select count(*) from fixture')).scalar() == 0:
        df = open('WPL/WPL2025.csv', 'r')
        df = list(csv.reader(df))
        for i in df[1:]:
            mt = Fixture(Match_No=i[0], Date=(datetime.strptime(i[1],'%d/%m/%Y')).date(),\
                                    Time=(datetime.strptime(i[2],'%H:%M:%S')).time(),\
                                    Team_A=i[3], Team_B=i[4], Venue=i[5],\
                                    A_info={'runs':0, 'overs':0.0, 'wkts':0},\
                                    B_info={'runs':0, 'overs':0.0, 'wkts':0})
            db.session.add(mt)
            db.session.commit()
    if db.session.execute(text('select count(*) from squad')).scalar() == 0:
        df = open('WPL/all teams squad wpl.csv', 'r')
        df = list(csv.reader(df))
        for i in df[1:]:
            pl = Squad(Player_ID=i[0], Name=i[1], Team=i[2], Captain=i[3], Keeper=i[4], Overseas=i[5],\
                       Role=i[6], Batting=i[7], Bowling=i[8], Nationality=i[9],\
                       DOB=(datetime.strptime(i[10],'%d/%m/%Y')).date())
            db.session.add(pl)
            db.session.commit()
    return render_template('index.html', teams=list(full_name.keys()), clr=clr)

@main.route('/pointstable')
def displayPT():
    dataPT = Pointstable.query.order_by(Pointstable.Points.desc(),Pointstable.NRR.desc()).all()
    dt = [['#', 'Logo', 'Teams', 'P', 'W', 'L', 'NR', 'Points', 'NRR', 'Last 5', 'Next Match'], [i for i in range(1,11)],\
         [], [], [], [], [], [], [], [], [], []]
    teams_ABV = []
    for i in dataPT:
        img = "/static/images/{}.png".format(i.team_name)
        dataFR = db.session.execute(
    text('SELECT Team_A, Team_B, Result FROM Fixture WHERE Team_A = :team OR Team_B = :team'),
                                                {'team': i.team_name}).fetchall()
        nm = '--'
        for j in dataFR:
            if j[2] != None:
                continue
            nm = j[0] if j[0] != i.team_name else j[1]
            nm = 'vs ' + nm
            break
        dt[2].append(img)
        teams_ABV.append(i.team_name)
        dt[3].append(full_name[i.team_name])
        dt[4].append(i.P)
        dt[5].append(i.W)
        dt[6].append(i.L)
        dt[7].append(i.NR)
        dt[8].append(i.Points)
        I = '{0:+}'.format(i.NRR)
        dt[9].append(I)
        wl = list(eval(i.Win_List).values())
        wl = wl if len(wl)<5 else wl[-5:]
        wl = list(wl)
        wl = ''.join(wl)
        dt[10].append(wl)
        dt[11].append(nm)
    return render_template('displayPT.html', PT=dt, TABV=teams_ABV, clr=ptclr)

@main.route('/fixtures')
def displayFR():
    team = request.args.get('team','All',type=str)
    if team == 'All':
        dataFR = db.session.execute(text('select * from Fixture'))\
            #Fixture.query.all()
        hint = 'All'
    else:
        dataFR = db.session.execute(text('SELECT * FROM Fixture WHERE Team_A = :team OR Team_B = :team'),{'team': team}).fetchall()
            #Fixture.query.filter_by(or_(Fixture.Team_A == team, Fixture.Team_B == team)).all()
        hint = team
    dt = [['Match No', 'Date', 'Venue', 'Team-A', 'Team-B', 'TA-Score', 'TB-Score', 'WT', 'WType', 'WBy']]
    for i in dataFR:
        dtt = []
        dtt.append(i[1]) #Match No
        dttm = datetime.strptime(i[2],'%Y-%m-%d').strftime('%Y-%m-%d')+' '+ \
                     datetime.strptime(i[3][:-7],'%H:%M:%S').strftime('%H:%M:%S')
        dtt.append(datetime.strptime(dttm, '%Y-%m-%d %H:%M:%S'))  #DateTime
        dtt.append(i[6].split(', ')[1])  #Venue
        dtt.append(i[4])  #Team A
        dtt.append(i[5])  #Team B
        A, B = eval(i[8]), eval(i[9])
        dtt.append(A) #TA_Scr
        dtt.append(B) #TB_Scr
        if i[10] is None:
            dtt.append('TBA') #Win-Team
            dtt.append('TBA')
            dtt.append('TBA')
        else:
            dtt.append(i[10])
            WType = 'wickets' if 'wickets' in i[7] else 'runs'
            dtt.append(WType)
            WBy = re.findall(r'\d+', i[7])[0]
            dtt.append(str(WBy))
        
        dt.append(dtt)
    for j in dt:
        print(j)
    current_date = datetime.now(tz)
    current_date = current_date.replace(tzinfo=None)
    return render_template('displayFR.html', FR=dt, hint=hint, fn=full_name, current_date=current_date, clr=clr)

@main.route('/teams')
def teams():
    return render_template('teams.html', fn=full_name, clr=clr)

@main.route('/<team>')
def squad(team):
    sq = Squad.query.filter_by(Team=team).order_by(Squad.Player_ID).all()
    for i in sq:
        print(i.Name)
    return render_template('squad.html', team=team, sq=sq, fn=full_name[team], clr=clr[team])

@main.route('/<team>/squad_details/<name>')
def squad_details(team, name):
    sq = Squad.query.filter_by(Name=name).first()
    return render_template('squad_details.html', sq=sq, clr=clr[team], team=team)

#@main.route('/liveScore')
#def liveScore():
#    current_date = date.today()
#    TodayFR = db.session.execute(text('SELECT * FROM Fixture WHERE date = :current_date'),{'current_date': current_date}).fetchall()
#    print(TodayFR)
#    print(len(TodayFR))
#    if len(TodayFR) != 0:
#        return render_template('no_live_match.html')
#    else:
#        return render_template('live.html')

@main.route('/liveScore')
def liveScore():
    return render_template('maintenance.html')

@main.route('/update')
@login_required
def update():
    FR = Fixture.query.all()
    if request.args.get('key'):
        key = request.args.get('key')
    else:
        key = None
    return render_template('update.html', key=key, FR=FR)

@main.route('/updatematch', methods=['POST'])
@login_required
def updatematch():
    hint = request.form.get('hint')
    key = 1
    if request.method == "POST" and hint == 'before':
        match = str(request.form.get('match')).upper()
        match = int(match) if match.isdigit() else pofs[match]
        FR = Fixture.query.filter_by(Match_No=match).first()
        if match not in [i for i in range(1,21)]+list(pofs.values()):
            flash('Invalid Match number to update', category='error')
            return redirect(url_for('main.update', key=key))
        if FR.Win_T != None:
            flash('Result for Match {} already updated, delete to update it again'.format(match), category='warning')
            return redirect(url_for('main.update', key=key))
        if FR.Team_A == 'TBA' or FR.Team_B == 'TBA':
            flash('Teams are not updated for Playoff Match {} to update its result'.format(match), category='warning')
            return redirect(url_for('main.update', key=key))
        return render_template('updatematch.html', FR=FR, fn=full_name, match=match)
    if request.method == 'POST' and hint == 'after':
        A = [int(request.form['runsA']), float(request.form['oversA']), int(request.form['wktsA'])]
        B = [int(request.form['runsB']), float(request.form['oversB']), int(request.form['wktsB'])]
        wt, win_type, win_by = str(request.form['wt']).upper(), str(request.form['win_type']), str(request.form['win_by'])
        result = '{} won by {} {}'.format(full_name[wt], win_by, win_type)
        match_no = request.form['match']
        FR = Fixture.query.filter_by(Match_No=str(match_no)).first()
        a, b = FR.Team_A,  FR.Team_B
        FR.Result = result
        FR.Win_T = wt
        FR.A_info, FR.B_info = {'runs':A[0], 'overs':A[1], 'wkts':A[2]}, {'runs':B[0], 'overs':B[1], 'wkts':B[2]}
        db.session.commit()
        if match_no.isdigit():
            A[1] = 20 if A[2] == 10 else A[1]
            B[1] = 20 if B[2] == 10 else B[1]
            dataA = db.session.execute(text('SELECT team_name, P, W, L, Points, For, Against, Win_List FROM pointstable WHERE team_name = :team_name'),{'team_name': str(a)}).fetchall()
            for i in dataA:
                if i[0] == wt:
                    P, W, L, Points = 1 + i[1], 1 + i[2], 0 + i[3], i[4] + 2
                    wl = eval(i[7])
                    wl[int(match_no)] = 'W'
                    wl = dict(sorted(wl.items()))
                else:
                    P, W, L, Points = 1 + i[1], 0 + i[2], 1 + i[3], i[4] + 0
                    wl = eval(i[7])
                    wl[int(match_no)] = 'L'
                    wl = dict(sorted(wl.items()))
                forRuns = eval(i[5])['runs'] + A[0]
                forOvers = oversAdd(eval(i[5])['overs'], A[1])
                againstRuns = eval(i[6])['runs'] + B[0]
                againstOvers = oversAdd(eval(i[6])['overs'], B[1])
                NRR = round((forRuns / ovToPer(forOvers) - againstRuns / ovToPer(againstOvers)), 3)
            PT = Pointstable.query.filter_by(team_name=str(a)).first()
            PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
            PT.For = {"runs": forRuns, "overs": forOvers}
            PT.Against = {"runs": againstRuns, "overs": againstOvers}
            db.session.commit()

            dataB = db.session.execute(text('SELECT team_name, P, W, L, Points, For, Against, Win_List FROM pointstable WHERE team_name = :team_name'),{'team_name': str(b)}).fetchall()
            for i in dataB:
                if i[0] == wt:
                    P, W, L, Points = 1 + i[1], 1 + i[2], 0 + i[3], i[4] + 2
                    wl = eval(i[7])
                    wl[int(match_no)] = 'W'
                    wl = dict(sorted(wl.items()))
                else:
                    P, W, L, Points = 1 + i[1], 0 + i[2], 1 + i[3], i[4] + 0
                    wl = eval(i[7])
                    wl[int(match_no)] = 'L'
                    wl = dict(sorted(wl.items()))
                forRuns = eval(i[5])['runs'] + B[0]
                forOvers = oversAdd(eval(i[5])['overs'], B[1])
                againstRuns = eval(i[6])['runs'] + A[0]
                againstOvers = oversAdd(eval(i[6])['overs'], A[1])
                NRR = round((forRuns / ovToPer(forOvers) - againstRuns / ovToPer(againstOvers)), 3)
            PT = Pointstable.query.filter_by(team_name=str(b)).first()
            PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
            PT.For = {"runs": forRuns, "overs": forOvers}
            PT.Against = {"runs": againstRuns, "overs": againstOvers}
            db.session.commit()
        flash('Match {} result updated successfully'.format(match_no), category='success')
        return redirect(url_for('main.update', key=key))

@main.route('/deletematch', methods=['POST'])
@login_required
def deletematch():
    hint = request.form.get('hint')
    key = 2
    if request.method == "POST" and hint == 'before':
        dmatch = str(request.form.get('dmatch')).upper()
        dmatch = int(dmatch) if dmatch.isdigit() else pofs[dmatch]
        FR = Fixture.query.filter_by(Match_No=dmatch).first()
        if dmatch not in [i for i in range(1, 21)] + list(pofs.values()):
            flash('Invalid Match number to delete', category='error')
            return redirect(url_for('main.update', key=key))
        if FR.Win_T == None:
            flash('Result for Match {} is not yet updated to delete'.format(dmatch), category='warning')
            return redirect(url_for('main.update', key=key))
        return render_template('deletematch.html', FR=FR, fn=full_name, dmatch=dmatch)
    if request.method == "POST" and hint == 'after':
        dmatch = request.form.get('dmatch')
        if dmatch.isdigit():
            FR = db.session.execute(text('SELECT Team_A, Team_B, A_info, B_info, Win_T FROM fixture WHERE Match_No = :match_no'),{'match_no': dmatch}).fetchall()
            for i in FR:
                A = list(eval(i[2]).values())
                B = list(eval(i[3]).values())
                A = [int(A[0]), float(A[1]), int(A[2])]
                B = [int(B[0]), float(B[1]), int(B[2])]
                wt = i[4]
                a, b = i[0], i[1]
            A[1] = 20 if A[2] == 10 else A[1]
            B[1] = 20 if B[2] == 10 else B[1]

            dataA = db.session.execute(text('SELECT team_name, P, W, L, Points, "For", "Against", Win_List FROM pointstable WHERE team_name = :team_name'),{'team_name': str(a)}).fetchall()

            for i in dataA:
                if i[0] == wt:
                    P, W, L, Points = i[1] - 1, i[2] - 1, i[3] - 0, i[4] - 2
                    wl = eval(i[7])
                    del wl[int(dmatch)]
                    wl = dict(sorted(wl.items()))
                else:
                    P, W, L, Points = i[1] - 1, i[2] - 0, i[3] - 1, i[4] - 0
                    wl = eval(i[7])
                    del wl[int(dmatch)]
                    wl = dict(sorted(wl.items()))
                forRuns = eval(i[5])['runs'] - A[0]
                forOvers = oversSub(eval(i[5])['overs'], A[1])
                againstRuns = eval(i[6])['runs'] - B[0]
                againstOvers = oversSub(eval(i[6])['overs'], B[1])
                if ovToPer(forOvers) == 0 or ovToPer(againstOvers) == 0:
                    NRR = 0.0
                else:
                    NRR = round((forRuns / ovToPer(forOvers) - againstRuns / ovToPer(againstOvers)), 3)
            PT = Pointstable.query.filter_by(team_name=str(a)).first()
            PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
            PT.For = {"runs": forRuns, "overs": forOvers}
            PT.Against = {"runs": againstRuns, "overs": againstOvers}
            db.session.commit()


            dataB = db.session.execute(text('SELECT team_name, P, W, L, Points, "For", "Against", Win_List FROM pointstable WHERE team_name = :team_name'),{'team_name': str(b)}).fetchall()
            for i in dataB:
                if i[0] == wt:
                    P, W, L, Points = i[1] - 1, i[2] - 1, i[3] - 0, i[4] - 2
                    wl = eval(i[7])
                    del wl[int(dmatch)]
                    wl = dict(sorted(wl.items()))
                else:
                    P, W, L, Points = i[1] - 1, i[2] - 0, i[3] - 1, i[4] - 0
                    wl = eval(i[7])
                    del wl[int(dmatch)]
                    wl = dict(sorted(wl.items()))
                forRuns = eval(i[5])['runs'] - B[0]
                forOvers = oversSub(eval(i[5])['overs'], B[1])
                againstRuns = eval(i[6])['runs'] - A[0]
                againstOvers = oversSub(eval(i[6])['overs'], A[1])
                if ovToPer(forOvers) == 0 or ovToPer(againstOvers) == 0:
                    NRR = 0.0
                else:
                    NRR = round((forRuns / ovToPer(forOvers) - againstRuns / ovToPer(againstOvers)), 3)
            PT = Pointstable.query.filter_by(team_name=str(b)).first()
            PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
            PT.For = {"runs": forRuns, "overs": forOvers}
            PT.Against = {"runs": againstRuns, "overs": againstOvers}
            db.session.commit()

        FR = Fixture.query.filter_by(Match_No=dmatch).first()
        FR.Result = None
        FR.Win_T = None
        FR.A_info, FR.B_info = {'runs': 0, 'overs': 0.0, 'wkts': 0}, {'runs': 0, 'overs': 0.0, 'wkts': 0}
        db.session.commit()
        flash('Match {} result deleted successfully'.format(dmatch), category='success')
        return redirect(url_for('main.update', key=key))

@main.route('/updateplayoffs', methods=['POST'])
@login_required
def updateplayoffs():
    hint = request.form.get('hint')
    key = 3
    if request.method == "POST" and hint == 'before':
        pomatch = request.form.get('pomatch').upper()
        if pomatch not in [str(i) for i in range(1, 21)] + ['Q1', 'E', 'Q2', 'F']:
            flash('Invalid match, Select a valid Playoff Match', category='error')
            return redirect(url_for('main.update', key=key))
        FR = Fixture.query.filter_by(Match_No=pofs[pomatch]).first()
        return render_template('playoffsupdate.html', pomatch=pofs[pomatch], teams=full_name, FR=FR)
    if request.method == 'POST' and hint == 'after':
        pomatch = request.form.get('pomatch')
        FR = Fixture.query.filter_by(Match_No=pomatch).first()
        if request.form.get('checkA') == 'YES':
            FR.Team_A = request.form.get('teamA')
        if request.form.get('checkB') == 'YES':
            FR.Team_B = request.form.get('teamB')
        if request.form.get('checkV') == 'YES':
            FR.Venue = request.form.get('venue')
        db.session.commit()
        flash('{} Playoff teams updated successfully'.format(pomatch), category='success')
        return redirect(url_for('main.update', key=key))


