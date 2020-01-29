from flask import Flask, url_for, redirect, render_template, request, abort, send_from_directory, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import exists, func, update
from sqlalchemy.orm import aliased
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
import random
import re
from sqlalchemy import desc, asc

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'


@login.user_loader
def load_user(id):
    return User.query.get(id)


class Base(db.Model):
    __abstract__ = True

    def add(self):
        try:
            db.session.add(self)
            self.save()
        except:
            db.session.rollback()

    def save(self):
        try:
            db.session.commit()
        except:
            db.session.rollback()

    def delete(self):
        try:
            db.session.delete(self)
            self.save()
        except:
            pass


from app.bp_events.controllers import events
from app.bp_api.controllers import api

app.register_blueprint(events, url_prefix="/events")
app.register_blueprint(api, url_prefix="/api")

from app.models import User, UserProfile
from app.models import Quest, QuestsAccepted, QuestCoinsTransaction, QuestComments
from app.models import Seek, SeeksAccepted, SeekCoinsTransaction, SeekComments
from app.models import Avatars, UserAvatars
from app.forms import LoginForm, SignUpForm, QuestForm, SeekForm, QuestCommentsForm, SeekCommentsForm

db.create_all()


@app.context_processor
def inject_dict_for_all_templates():
    if (not current_user.is_anonymous):
        userprofile = (db.session.query(UserProfile)
                       .filter(UserProfile.id == current_user.id)
                       .first()
                       )
        return dict(current_user_avatar=userprofile.avatarId)

    return dict()


@app.route('/complete/<id>', methods=["POST"])
def complete(id):
    if request.method == 'POST':
        user = User.query.filter_by(id=request.form['user']).first()
        userProfile = UserProfile.query.filter_by(id=user.id).first()

        if id.startswith('Q'):
            q = Quest.query.filter_by(questId=id).first()
            reward = q.reward

            # add user to questsCompleted table
            questTransaction = QuestCoinsTransaction(questId=id, userId=user.id, coins=reward)
            db.session.add(questTransaction)
            db.session.commit()

            coinsBefore = userProfile.coinsCollected

            # give reward to user
            db.session.query(UserProfile).filter(UserProfile.id == user.id). \
                update({"coinsBalance": (UserProfile.coinsBalance + reward)})
            db.session.query(UserProfile).filter(UserProfile.id == user.id). \
                update({"coinsCollected": (UserProfile.coinsCollected + reward)})

            coinsAfter = userProfile.coinsCollected
            coinsToNext = userProfile.coinsCollected % 20

            if (int(coinsAfter / 20) > int(coinsBefore / 20)):
                db.session.query(UserProfile).filter(UserProfile.id == user.id). \
                    update({"level": UserProfile.level + 1})

            if (coinsToNext == 0):
                coinsToNext = 20

            db.session.query(UserProfile).filter(UserProfile.id == user.id). \
                update({"coinsToNext": coinsToNext})

            db.session.commit()

            return redirect(url_for('quest'))

        if id.startswith('S'):
            q = Seek.query.filter_by(seekId=id).first()

            # add user to questsCompleted table
            seekTransaction = SeekCoinsTransaction(seekId=id, userId=user.id)
            db.session.add(seekTransaction)
            db.session.commit()

            # give reward to poster
            reward = q.reward

            db.session.query(UserProfile).filter(UserProfile.id == current_user.id). \
                update({"coinsBalance": (UserProfile.coinsBalance + reward)})
            db.session.query(UserProfile).filter(UserProfile.id == current_user.id). \
                update({"coinsCollected": (UserProfile.coinsCollected + reward)})
            db.session.commit()

            return redirect(url_for('seek'))


@app.route('/delete/<id>', methods=["POST"])
def delete(id):
    # print(id)
    if id.startswith('Q'):
        db.session.query(Quest).filter(Quest.questId == id).update({"state": 2})
        db.session.commit()
        return redirect(url_for('quest'))

    elif id.startswith('S'):
        db.session.query(Seek).filter(Seek.seekId == id).update({"state": 2})
        db.session.commit()
        return redirect(url_for('seek'))


@app.route('/accept/<id>', methods=["POST"])
def accept(id):
    if id.startswith('Q'):
        qa = QuestsAccepted(questId=id, userId=current_user.get_id())
        db.session.add(qa)
        db.session.commit()

    elif id.startswith('S'):

        sa = SeeksAccepted(seekId=id, userId=current_user.get_id())
        db.session.add(sa)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/forfeit/<id>', methods=["POST"])
def forfeit(id):
    if id.startswith('Q'):
        qf = (db.session.query(User, QuestsAccepted)
              .filter(User.id == QuestsAccepted.userId)
              .filter(User.id == current_user.get_id())
              .filter(QuestsAccepted.questId == id)
              .first())

        db.session.delete(qf[1])
        db.session.commit()

    elif id.startswith('S'):
        sf = (db.session.query(User, SeeksAccepted)
              .filter(User.id == SeeksAccepted.userId)
              .filter(User.id == current_user.get_id())
              .filter(SeeksAccepted.seekId == id)
              .first())

        db.session.delete(sf[1])
        db.session.commit()

    return redirect(url_for('home'))


# home
@app.route('/')
def index():
    if (not current_user.is_anonymous):
        questsCreated = (db.session.query(User, Quest)
                         .filter(User.id == Quest.userId)
                         .filter(Quest.userId == current_user.get_id())
                         .filter(Quest.state == 0)
                         .order_by(Quest.posted_at.desc())
                         .all())
        return render_template('index.html', rows=questsCreated, page='home')
    return render_template('index.html', rows=None, page='home')


@app.route('/home')
def home():
    return index()


@app.route('/home/YourQuests')
def home_your_quests():
    return index()


@app.route('/home/YourSeeks')
def home_your_seeks():
    if (not current_user.is_anonymous):
        seeksCreated = (db.session.query(User, Seek)
                        .filter(User.id == Seek.userId)
                        .filter(Seek.userId == current_user.get_id())
                        .order_by(Seek.posted_at.desc())
                        .all())

        return render_template('index.html', rows=seeksCreated, page='ys')

    return index()


@app.route('/home/QuestsAccepted')
def home_quests_accepted():
    if (not current_user.is_anonymous):
        questsAccepted = (db.session.query(User, Quest, QuestsAccepted)
                          .filter(User.id == Quest.userId)
                          .filter(QuestsAccepted.questId == Quest.questId)
                          .filter(QuestsAccepted.userId == current_user.get_id())
                          .order_by(Quest.posted_at.desc())
                          .all())

        return render_template('index.html', rows=questsAccepted, page='qa')

    return index()


@app.route('/home/SeeksAccepted')
def home_seeks_accepted():
    if (not current_user.is_anonymous):
        seeksAccepted = (db.session.query(User, Seek, SeeksAccepted)
                         .filter(User.id == Seek.userId)
                         .filter(SeeksAccepted.seekId == Seek.seekId)
                         .filter(SeeksAccepted.userId == current_user.get_id())
                         .order_by(Seek.posted_at.desc())
                         .all())

        return render_template('index.html', rows=seeksAccepted, page='sa')

    return index()


@app.route('/quest')
def quest():
    q = (db.session.query(User, Quest)
         .filter(User.id == Quest.userId)
         .filter(Quest.state == 0)
         .filter(Quest.type == 0)
         .order_by(Quest.posted_at.desc())
         .all())

    return render_template('quest.html', rows=q, page='quest')


@app.route('/quest/HeroQuests')
def hero_quests():
    return redirect(url_for('quest'))


@app.route('/quest/SideQuests')
def side_quests():
    q = (db.session.query(User, Quest)
         .filter(User.id == Quest.userId)
         .filter(Quest.state == 0)
         .filter(Quest.type == 1)
         .order_by(Quest.posted_at.desc())
         .all())
    return render_template('quest.html', rows=q, page='sq')


@app.route('/quest/<id>')
def nextQuest(id):
    q = (db.session.query(User, Quest)
         .filter(User.id == Quest.userId)
         .filter(Quest.questId == id)
         .order_by(Quest.posted_at.desc())
         .first())

    # Get all that completed quest
    q1 = (db.session.query(User.id, User, QuestCoinsTransaction)
          .filter(QuestCoinsTransaction.questId == id)
          .filter(User.id == QuestCoinsTransaction.userId)
          .all()
          )

    q1id = (db.session.query(User.id)
            .filter(QuestCoinsTransaction.questId == id)
            .filter(User.id == QuestCoinsTransaction.userId)
            # .all()
            )

    # Get all users that accepted but not completed
    q2 = (db.session.query(User, QuestsAccepted)
          .filter(QuestsAccepted.questId == id)
          .filter(User.id == QuestsAccepted.userId)
          .filter(User.id.notin_(q1id))
          .all()
          )

    accepted = False
    completed = False

    if current_user.is_authenticated:
        # Check if current user already accepted quest
        acceptStatus = (db.session.query(User, QuestsAccepted)
                        .filter(User.id == current_user.id)
                        .filter(User.id == QuestsAccepted.userId)
                        .filter(QuestsAccepted.questId == id)
                        .first())

        if acceptStatus is not None:
            accepted = True

        # Check if current user already completed quest
        completeStatus = (db.session.query(User, QuestCoinsTransaction)
                          .filter(User.id == current_user.id)
                          .filter(User.id == QuestCoinsTransaction.userId)
                          .filter(QuestCoinsTransaction.questId == id)
                          .first())

        if completeStatus is not None:
            completed = True

    form = QuestCommentsForm()
    form.questId.data = id
    if current_user.is_authenticated:
        form.userId.data = current_user.id
        if (q[1].userId == current_user.id):
            form.is_creator.data = 1
        else:
            form.is_creator.data = 0

    comments = (db.session.query(QuestComments, User, UserProfile)
                .filter(User.id == QuestComments.userId)
                .filter(User.id == UserProfile.id)
                .order_by(QuestComments.posted_at.desc())
                .all()
                )
    # print(comments[0])

    return render_template('questDescription.html', quests=q, id=id,
                           accepted=accepted, completed=completed,
                           usersaccepted=q2, userscompleted=q1, comments=comments,
                           form=form)


@app.route('/questComment', methods=["POST"])
def questComment():
    if request.method == 'POST':
        questId = request.form['questId']
        userId = request.form['userId']
        is_creator = request.form['is_creator']
        description = request.form['description']
        # assign id to comment
        already = True
        while already:
            commentId = questId + str(random.randint(1, 30000))
            # check if id exists in DB
            idcheck = (db.session.query(QuestComments.commentId)
                       .filter(QuestComments.commentId == commentId)
                       .order_by(QuestComments.posted_at.desc())
                       .first()
                       )
            if idcheck is None:
                already = False

        qc = QuestComments(commentId=commentId, questId=questId, userId=userId, description=description,
                           is_creator=is_creator)
        db.session.add(qc)
        db.session.commit()
        return redirect(url_for('nextQuest', id=questId))


@app.route('/seek')
def seek():
    q = (db.session.query(User, Seek)
         .filter(User.id == Seek.userId)
         .filter(Seek.state == 0)
         .order_by(Seek.posted_at.desc())
         .all())
    return render_template('seek.html', rows=q, page='seek')


@app.route('/seek/<id>')
def nextSeek(id):
    q = (db.session.query(User, Seek)
         .filter(User.id == Seek.userId)
         .filter(Seek.seekId == id)
         .order_by(Seek.posted_at.desc())
         .first())

    # Get all that completed seek
    q1 = (db.session.query(User.id, User, SeekCoinsTransaction)
          .filter(SeekCoinsTransaction.seekId == id)
          .filter(User.id == SeekCoinsTransaction.userId)
          .all()
          )

    q1id = (db.session.query(User.id)
            .filter(SeekCoinsTransaction.seekId == id)
            .filter(User.id == SeekCoinsTransaction.userId)
            # .all()
            )

    # Get all users that accepted but not completed
    q2 = (db.session.query(User, SeeksAccepted)
          .filter(SeeksAccepted.seekId == id)
          .filter(User.id == SeeksAccepted.userId)
          .filter(User.id.notin_(q1id))
          .all()
          )

    accepted = False
    completed = False

    if current_user.is_authenticated:
        # Check if current user already accepted seek
        acceptStatus = (db.session.query(User, SeeksAccepted)
                        .filter(User.id == current_user.id)
                        .filter(User.id == SeeksAccepted.userId)
                        .filter(SeeksAccepted.seekId == id)
                        .first())

        if acceptStatus is not None:
            accepted = True

        # Check if current user already completed seek
        completeStatus = (db.session.query(User, SeekCoinsTransaction)
                          .filter(User.id == current_user.id)
                          .filter(User.id == SeekCoinsTransaction.userId)
                          .filter(SeekCoinsTransaction.seekId == id)
                          .first())

        if completeStatus is not None:
            completed = True

    form = SeekCommentsForm()
    form.seekId.data = id
    if current_user.is_authenticated:
        form.userId.data = current_user.id
        if (q[1].userId == current_user.id):
            form.is_creator.data = 1
        else:
            form.is_creator.data = 0

    comments = (db.session.query(SeekComments, User, UserProfile)
                .filter(User.id == SeekComments.userId)
                .filter(User.id == UserProfile.id)
                .order_by(SeekComments.posted_at.desc())
                .all())
    # print(comments[0])

    return render_template('seekDescription.html', seeks=q, id=id,
                           accepted=accepted, completed=completed,
                           usersaccepted=q2, userscompleted=q1, comments=comments, form=form)


@app.route('/seekComment', methods=["POST"])
def seekComment():
    if request.method == 'POST':
        seekId = request.form['seekId']
        userId = request.form['userId']
        is_creator = request.form['is_creator']
        description = request.form['description']
        # assign id to comment
        already = True
        while already:
            commentId = seekId + str(random.randint(1, 30000))
            # check if id exists in DB
            idcheck = (db.session.query(SeekComments.commentId)
                       .filter(SeekComments.commentId == commentId)
                       .order_by(SeekComments.posted_at.desc())
                       .first()
                       )
            if idcheck is None:
                already = False

        sc = SeekComments(commentId=commentId, seekId=seekId, userId=userId, description=description,
                          is_creator=is_creator)
        db.session.add(sc)
        db.session.commit()
    return redirect(url_for('nextSeek', id=seekId))


@app.route('/forms/quest', methods=["GET", "POST"])
def forms_quest():
    form = LoginForm()
    form2 = QuestForm()
    if not current_user.is_authenticated:
        return render_template('login.html', form=form)

    if request.method == 'POST':

        # assign id to quest
        already = True
        while already:
            questId = 'Q' + str(random.randint(1, 10000))

            # check if seek exists in DB
            idcheck = (db.session.query(Quest.questId)
                       .filter(Quest.questId == questId)
                       .first()
                       )
            if idcheck is None:
                already = False

        reward = 20
        item = request.form['item']
        location = request.form['location']
        description = request.form['description']
        type = request.form['type']
        user = User.query.filter_by(id=current_user.get_id()).first()
        print('here', item)
        quest = Quest(questId=questId, reward=reward,
                      item=item, location=location,
                      description=description, userId=user.id,
                      type=type)
        db.session.add(quest)
        db.session.commit()
        return redirect(url_for('nextQuest', id=questId, code=307))

    else:
        return render_template('forms.html', form=form2)


@app.route('/forms/seek', methods=["GET", "POST"])
def forms_seek():
    form = LoginForm()
    form2 = QuestForm()
    if not current_user.is_authenticated:
        return render_template('login.html', form=form)

    if request.method == 'POST':

        # assign id to seek
        already = True
        while already:
            seekId = 'S' + str(random.randint(1, 10000))
            print(seekId)
            # check if seek exists in DB
            idcheck = (db.session.query(Seek.seekId)
                       .filter(Seek.seekId == seekId)
                       .first()
                       )
            if idcheck is None:
                already = False

        reward = 20
        item = request.form['item']
        location = request.form['location']
        description = request.form['description']
        user = User.query.filter_by(id=current_user.get_id()).first()
        print('here', item)
        seek = Seek(seekId=seekId, reward=reward,
                    item=item, location=location,
                    description=description, userId=user.id)
        db.session.add(seek)
        db.session.commit()
        return redirect(url_for('nextSeek', id=seekId, code=307))

    else:
        return render_template('forms.html', form=form2, page='sf')


@app.route('/edit/<id>', methods=["GET", "POST"])
def edit(id):
    # user = current_user
    if request.method == 'POST':

        try:
            # take form data
            item = request.form['item']
            location = request.form['location']
            description = request.form['description']

            print(id)
            if id.startswith('Q'):
                # make changes to Quest
                db.session.query(Quest) \
                    .filter(Quest.questId == id). \
                    update({"item": item})
                db.session.query(Quest) \
                    .filter(Quest.questId == id). \
                    update({"location": location})
                db.session.query(Quest) \
                    .filter(Quest.questId == id). \
                    update({"description": description})
                db.session.commit()
                print('cde')
                return redirect(url_for('nextQuest', id=id, code=307))

            elif id.startswith('S'):
                print('here')
                # make changes to Seek
                db.session.query(Seek) \
                    .filter(Seek.seekId == id). \
                    update({"item": item})
                db.session.query(Seek) \
                    .filter(Seek.seekId == id). \
                    update({"location": location})
                db.session.query(Seek) \
                    .filter(Seek.seekId == id). \
                    update({"description": description})
                db.session.commit()
                print('cde')
                return redirect(url_for('nextSeek', id=id, code=307))
        except:
            if id.startswith('Q'):
                quest = Quest.query.filter_by(questId=id).first()
                form = QuestForm()
                form.item.data = quest.item
                form.location.data = quest.location
                form.description.data = quest.description
                return render_template('edit.html', id=id, form=form, code=307)

            elif id.startswith('S'):
                print('error')
                seek = Seek.query.filter_by(seekId=id).first()
                form = SeekForm()
                form.item.data = seek.item
                form.location.data = seek.location
                form.description.data = seek.description
                return render_template('edit.html', id=id, form=form, code=307)



@app.route('/faq')
def faq():
    return render_template('faq.html', page='faq')


@app.route('/faq/general')
def faq_general():
    return redirect(url_for('faq'))


@app.route('/faq/points_system')
def faq_points_system():
    return render_template('faq.html', page='points_system')


@app.route('/faq/seekers')
def faq_seekers():
    return render_template('faq.html', page='seekers')


@app.route('/leaderboard')
def leaderboard():
    # get all counts
    q1 = (db.session.query(User, func.count(QuestCoinsTransaction.questId).label('amt'))
          .group_by(User.id)
          .filter(User.id == QuestCoinsTransaction.userId)
          )

    # combine counts with user,userprofile
    q1s = q1.subquery()
    q2 = (db.session.query(User, UserProfile, q1s.c.amt)
          .outerjoin(q1s, User.id == q1s.c.id)
          .filter(User.id == UserProfile.id)
          .order_by(UserProfile.coinsCollected.desc())
          .all()
          )

    print(q2)

    return render_template('leaderboard.html', query=q2, page='leaderboard')


@app.route('/profile')
def profile():
    user = current_user
    userprofile = UserProfile.query.filter_by(id=user.id).first()
    return render_template('profile.html', user=user, userprofile=userprofile)


@app.route('/profile/general')
def profile_general():
    return redirect(url_for('profile'))


@app.route('/profile/avatars')
def profile_avatars():
    user = current_user
    userprofile = (db.session.query(UserProfile, Avatars)
                   .filter(UserProfile.id == user.id)
                   .filter(UserProfile.avatarId == Avatars.avatarId)
                   .first()
                   )

    print(userprofile)

    # UserProfile.query.filter_by(id=user.id).first()
    avatars = db.session.query(Avatars).all()
    ua = (db.session.query(UserAvatars.avatarId)
          .filter(user.id == UserAvatars.userId)
          .all())
    user_avatars = []
    for i in ua:
        user_avatars.append(i[0])

    return render_template('profile.html', user=user, userprofile=userprofile, page='avatars', avatars=avatars,
                           user_avatars=user_avatars)


@app.route('/profile/avatars/update/<avatarId>', methods=["GET", "POST"])
def profile_avatars_update(avatarId):
    user = current_user
    if request.method == 'POST':
        db.session.query(UserProfile) \
            .filter(UserProfile.id == user.id). \
            update({"avatarId": avatarId})
        db.session.commit()

    return redirect(url_for('profile_avatars'))


@app.route('/profile/avatars/unlock/<avatarId>', methods=["GET", "POST"])
def profile_avatars_unlock(avatarId):
    user = current_user
    if request.method == 'POST':
        userProfile = (db.session.query(UserProfile)
                       .filter(user.id == UserProfile.id)
                       .first())

        avatar = (db.session.query(Avatars)
                  .filter(avatarId == Avatars.avatarId)
                  .first())
        print(avatar)

        # if enough coins
        if userProfile.coinsBalance >= avatar.coinsRequired:
            db.session.query(UserProfile).filter(UserProfile.id == user.id). \
                update({"coinsBalance": (UserProfile.coinsBalance - avatar.coinsRequired)})
            user_avatar = UserAvatars(avatarId=avatarId, userId=user.id)
            db.session.add(user_avatar)
            db.session.commit()

    return redirect(url_for('profile_avatars'))


@app.route('/profile/badges')
def profile_badges():
    user = current_user
    userprofile = UserProfile.query.filter_by(id=user.id).first()

    return render_template('profile.html', user=user, userprofile=userprofile, page='badges')


@app.route('/settings', methods=["GET", "POST"])
def settings():
    user = current_user
    if request.method == 'POST':
        # take form data
        email = request.form['email']
        username = request.form['username']
        print(username)
        # Check if email format correct
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
        if match == None:
            # print('Bad Syntax')
            form = SignUpForm()
            return render_template('signup.html', form=form, err="invalid username or password")
        # Check if email and username already in use
        userEmail = User.query.filter_by(email=email).first()
        userUsername = User.query.filter_by(username=username).first()
        if userEmail is not None and userUsername is not None:
            userprofile = UserProfile.query.filter_by(id=user.id).first()
            form = SignUpForm()
            form.username.data = user.username
            form.email.data = user.email
            return render_template('settings.html', user=user, userprofile=userprofile, form=form)

        # make changes to user in DB
        db.session.query(User) \
            .filter(User.id == user.id). \
            update({"username": username})

        db.session.query(User) \
            .filter(User.id == user.id). \
            update({"email": email})

        print('here', current_user.username)
        db.session.commit()
        return redirect(url_for('settings'))
    else:
        userprofile = UserProfile.query.filter_by(id=user.id).first()
        form = SignUpForm()
        form.username.data = user.username
        form.email.data = user.email
        return render_template('settings.html', user=user, userprofile=userprofile, form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        currUser = User.query.filter_by(username=username).first()

        # check if user exists in db and if password is correct
        if currUser is None or password != currUser.password:
            return render_template('login.html', form=form, err="invalid username or password")
        user = currUser
        login_user(user, remember=user)
        flash("Log in successful!")
        # print(user.email, user.username, user.password)
        return redirect(url_for('index'))
    else:
        return render_template('login.html', form=form)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    form2 = SignUpForm()
    if request.method == 'POST':
        # else go to email, pass
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        # Check if email format correct
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
        if match == None:
            # print('Bad Syntax')
            return render_template('signup.html', form=form2, err="invalid username or password")
        # Check if email and username already in use
        userEmail = User.query.filter_by(email=email).first()
        userUsername = User.query.filter_by(username=username).first()
        if userEmail is not None or userUsername is not None:
            return render_template('signup.html', form=form2, err="invalid username or password")
        # Check if password equals confirm password
        if password != confirm:
            flash('Passwords do not match!')
            return render_template('signup.html', form=form2, err="invalid username or password")

        # assign id to user
        already = True
        while already:
            id = 'U' + str(random.randint(1, 10001))
            # check if id exists in DB
            idcheck = (db.session.query(User.id)
                       .filter(User.id == id)
                       .first()
                       )
            if idcheck is None:
                already = False

        user = User(id=id, email=email, password=password, username=username)
        userprofile = UserProfile(id=id)
        user_avatar = UserAvatars(avatarId='0000', userId=id)
        login_user(user, remember=user)

        # store user in DB
        db.session.add(user)
        db.session.add(userprofile)
        db.session.add(user_avatar)
        db.session.commit()
        flash("Signup in successful!")
        # print(User.query.all())
        return redirect(url_for('index'))
    else:
        return render_template('signup.html', form=form2)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/create')
def create():
    # Create avatar data
    avatar_data = [['0000', 'Eggsy(Default)', 0],
                   ['0001', 'Wilson', 50],
                   ['0002', 'Lady', 50],
                   ['0003', 'Rave', 75],
                   ['0004', 'Barry', 50],
                   ['0005', 'McDuck', 75],
                   ['0006', 'Coco Jumbo', 50],
                   ['0007', 'Wednesday', 75],
                   ['0008', 'P.Sherman', 50],
                   ['0009', 'Bluetterfly', 75],
                   ]

    for i in avatar_data:
        u = Avatars(avatarId=i[0], name=i[1], coinsRequired=i[2])
        db.session.add(u)

    # give money etc
    # db.session.query(UserProfile).filter(UserProfile.id == current_user.id). \
    #     update({"coinsBalance": (UserProfile.coinsBalance + 200)})

    # user_avatar = UserAvatars(avatarId='0001', userId='U22')
    # db.session.add(user_avatar)
    db.session.commit()

    # q = db.session.query(Avatars).all()
    # print(q)
    # print(q[0].name, q[0].avatarId)
    # return (str(q))
    return ('beep')
