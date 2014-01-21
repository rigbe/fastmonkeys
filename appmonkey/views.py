from flask import jsonify,render_template, flash, redirect,session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from appmonkey import app,db,lm
from models import Monkey
from forms import RegistrationForm,LoginForm,EditForm,SearchForm
from werkzeug import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import or_



@lm.user_loader
def load_user(mid):
    return Monkey.query.get(int(mid))

    
@app.before_request
def before_request():
    g.user = current_user


@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET', 'POST'])
@login_required
def index(page = 1):
    allfriends=g.user.friends_of()
    return render_template('index.html',user=g.user,
        title = 'Home',
        friends = allfriends)



@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        newmonkey = Monkey(form.username.data,form.name.data,form.dob.data,form.email.data,form.password.data)
        db.session.add(newmonkey)
        db.session.commit()
        session['username']=newmonkey.username
        flash('Thanks for registering')
        return redirect(url_for('login'))
    return render_template('signup.html', 
        title = 'Sign up',
        form = form)




@app.route('/login', methods = ['GET', 'POST'])
def login():
    #so not to require a user who has already logged in to log in again
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        #first()makes monkey an object and not a BASEQUERy
        monkey = Monkey.query.filter_by(username = form.username.data).first()
        if monkey and monkey.check_password(form.password.data) :
            login_user(monkey)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash("Wrong username and/or password! Please try again.")
    
    return render_template('login.html', 
        title = 'Sign In',
        form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/monkey/<uname>',methods = ['GET', 'POST'])
@login_required
def monkey(uname):
    form=SearchForm()
    if form.validate_on_submit():
        uname=form.search.data
        monkey = Monkey.query.filter(or_(Monkey.username == uname,Monkey.name==uname)).first()
        if monkey == None:
            flash('Monkey ' + uname + ' not found.')
            return redirect(url_for('monkey',uname=g.user.username))
        else:
            uname=monkey.username  #if the searched monkey is found we show its profile but what is displayed 
            return redirect(url_for('monkey', uname = uname)) #in the profile depends on the logged monkey and its relation wz the monkey searched(r they friends?etc)
     
    monkey = Monkey.query.filter_by(username = uname).first()
    if monkey == None:
        flash('Monkey ' + uname + ' not found.')
        return redirect(url_for('index'))
    
    age=datetime.today().year - monkey.dob.year
    profileinfo= {'name':monkey.name,'email':monkey.email,'age':age}
    
    return render_template('user.html',
        monkey = monkey,
        profile = profileinfo,form=form)

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        g.user.name = form.name.data
        g.user.email = form.email.data
        g.user.dob = form.dob.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else: #form is already filled from the database in the start
        form.name.data = g.user.name
        form.email.data = g.user.email
        form.dob.data = g.user.dob
    return render_template('edit.html',
        form = form)



@app.route('/deactivate')
@login_required
def deactivate():
    #if g.user deactivates itself, we no more want it to be referenced as bestfriend for any users
    #and since is not handled when the delete is carried out, we remove all its reference this way
    bestfriends=Monkey.query.filter_by(bestfriendid=g.user.mid).all()
    for bests in bestfriends:
        bests.remove_bestfriend(g.user,bests.mid)
    #this will result in a cascade in the MonkeyFriend table in that it removes all friendships\
    #associated with the to be deleted g.user    
    db.session.delete(g.user)  
    db.session.commit()
    flash('You are no longer a member of fastmonkeys.')
    return redirect(url_for('logout'))


@app.route('/befriend/<uname>')
@login_required
def befriend(uname):
    user = Monkey.query.filter_by(username = uname).first()
    if user == None:
        flash('Monkey ' + uname + ' not found.')
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t befriend yourself!')
        return redirect(url_for('monkey', uname = uname))
    u = g.user.make_friend(user)
    if u is None:
        flash('Can not be friends with  ' + uname + '.')
        return redirect(url_for('monkey', uname = uname))
    db.session.add(u)
    db.session.commit()
    flash('You are now friends with ' + uname + '!')
    return redirect(url_for('monkey', uname = uname))

@app.route('/unfriend/<uname>')
@login_required
def unfriend(uname):
    user = Monkey.query.filter_by(username = uname).first()
    if user == None:
        flash('Monkey ' + uname + ' not found.')
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfriend yourself!')
        return redirect(url_for('monkey', uname = uname))
    u = g.user.remove_friend(user)
    
    if u is None:
        flash('Cannot unfriend' + uname + '.')
        return redirect(url_for('monkey', uname = uname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped being friends with ' + uname + '.')
    #if g.user unfriends user it must automatically stop being g.user's bestfriend incase it was
    if g.user.besty_with(user):
        unbest=g.user.remove_bestfriend(user,g.user.mid)
        db.session.add(unbest)
        db.session.commit()
        flash('You are no more bestys with' + '  ' + uname + '.')
    return redirect(url_for('monkey', uname = uname))


@app.route('/make_besty/<uname>')
@login_required
def make_besty(uname):
    user = Monkey.query.filter_by(username = uname).first()
    if user == None:
        flash('Monkey ' + uname + ' not found.')
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t be besty with yourself!')
        return redirect(url_for('monkey', uname = uname))
    u = g.user.make_bestfriend(user,g.user.mid)
    if u is None:
        flash('Cannot be bestys with ' + uname + '.')
        return redirect(url_for('monkey', uname = uname))
    db.session.add(u)
    db.session.commit()
    flash('You are now bestys with' +' '+ uname + '!')
    return redirect(url_for('monkey', uname = uname))

@app.route('/un_bestfriend/<uname>')
@login_required
def un_bestfriend(uname):
    user = Monkey.query.filter_by(username = uname).first()
    if user == None:
        flash('Monkey ' + uname + ' not found.')
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unbestfriend with yourself!')
        return redirect(url_for('monkey', uname = uname))
    u = g.user.remove_bestfriend(user,g.user.mid)
    if u is None:
        flash('Cannot unbestfriend ' + uname + '.')
        return redirect(url_for('monkey', uname = uname))
    db.session.add(u)
    db.session.commit()
    flash('You are no more bestys with' +'  ' + uname + '!')
    return redirect(url_for('monkey', uname = uname))
