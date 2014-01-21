from appmonkey import db
from werkzeug import generate_password_hash, check_password_hash
from sqlalchemy import update, or_

MonkeyFriend = db.Table('MonkeyFriend',
    db.Column('mid1', db.Integer, db.ForeignKey('monkey.mid')),
    db.Column('mid2', db.Integer, db.ForeignKey('monkey.mid'))
)

class Monkey(db.Model):
    mid = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    password = db.Column(db.String(256))
    name = db.Column(db.String(64), index = True)
    dob = db.Column(db.DateTime)
    email = db.Column(db.String(120), index = True, unique = True)
    bestfriendid=db.Column(db.Integer)
    friended = db.relationship('Monkey', 
        secondary = MonkeyFriend, 
        primaryjoin = (MonkeyFriend.c.mid1 == mid), 
        secondaryjoin = (MonkeyFriend.c.mid2 == mid), 
        backref = db.backref('friends', lazy = 'dynamic'), 
        lazy = 'dynamic')

    def __init__(self,username,name,dob,email,password):
        self.username = username
        self.name = name
        self.dob=dob
        self.email = email.lower()
        self.set_password(password)
     
    def set_password(self, password):
        self.password = generate_password_hash(password)
   
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.mid)

    def make_friend(self, user):
        if not self.is_friend(user):
            self.friended.append(user)
            return self

    def remove_friend(self, user):
        if self.is_friend(user):
            self.friended.remove(user)#this is for removing user that self befriended
            self.friends.remove(user) #this is because incase self wants to unfriend someone who befriended him instead of him befriending that someone
            return self

    def is_friend(self, user):
        #we check if self and user are friends by checking friended(if self has befriended user, secondary join) 
        #and also by checking friends(if user has befriended self, the primary join)
        if self.friended.filter(MonkeyFriend.c.mid1 == self.mid , MonkeyFriend.c.mid2 == user.mid).count()>0 or\
                self.friends.filter(MonkeyFriend.c.mid1 == user.mid , MonkeyFriend.c.mid2 == self.mid).count()>0:
            return True
        else:
            return False

        
    def make_bestfriend(self,user,selfid):
        if not self.besty_with(user):
            self.query.filter_by(mid=selfid).update({'bestfriendid':user.mid})
            return self
        
    def remove_bestfriend(self,user,selfid):
        
        if self.besty_with(user):
            
            self.query.filter_by(mid=selfid).update({'bestfriendid':None})
            return self

    def besty_with(self,user):
        #if we dont put the first rule, it will return true if the userid is listed as a bestfriendid anywhere in the table
        #but we want to make sure that user is indeed bestfriends with the particular g.user not with anyone else
        s=self.query.filter_by(mid=self.mid , bestfriendid=user.mid).first()
        if s:
            return True
        else:
            return False
            
    def has_besty(self):
        #besides checking if a bestfriendid exists, we should also check that bestfriendid is an id of a user still in the system
        if self.bestfriendid != None and self.query.filter_by(mid=self.bestfriendid).first() !=None:
            return True
        else:
            return False

    def besty(self):
        bff_id=self.bestfriendid
        bff=self.query.filter_by(mid=bff_id).first()
        if bff:
            return bff.name
        else:
            return None

    def friends_of(self):
        #all the friends who has been befriended by and also has befriended self
        return self.friended.all() + self.friends.all()       

    def count_friends(self):
        return len(self.friends_of())
        
        

       

