import os
import copy
from flask import Flask, render_template, send_from_directory
from flask import url_for, request, session, redirect
from flask_oauth import OAuth

from db import models

# initialization
app = Flask(__name__)
app.config.update(
    DEBUG = True,
)
app.config["SECRET_KEY"] = 'swe600'

# controllers
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
def index():
    return render_template('index.html')

#@app.route("/")
#def hello():
#    return "Hello from Python!"

# facebook authentication

FACEBOOK_APP_ID = '145630202496114'
FACEBOOK_APP_SECRET = '94855358208309d08a84b3f3a130c792'

oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/v2.5',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email,public_profile,user_friends'}
)

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

def pop_login_session():
    s=copy.deepcopy(session)
    for i in s:
        session.pop(i, None)
#    session.pop('logged_in', None)
#    session.pop('facebook_token', None)

@app.route("/facebook_login")
def facebook_login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)

    session['logged_in'] = True
    session['facebook_token'] = (resp['access_token'], '')
    data = facebook.get('/me?fields=id,name,first_name,last_name,gender,timezone,verified,friends,email').data
    print data
    required_fields = ['id', 'name', 'first_name', 'last_name', 'gender',
                       'timezone', 'verified', 'friends', 'email']
    user_data = dict()
    for i in required_fields:
        session[i] = data[i]
        if i == 'friends':
            user_data['friends_count'] = data[i]['summary']['total_count']
        elif i == 'id':
            user_data['facebook_id'] = data[i]
        else:
            user_data[i] = data[i]
    print user_data
    save_user_to_db(user_data)
    whole_user_data = get_user_from_db(session['id'])
    session['major'] = whole_user_data.major
    next_url = request.args.get('next') or url_for('index')
    return redirect(next_url)

@app.route("/extra_userdata", methods=["POST"])
def upload_extra_user_data():
    print(request.form["extra_userdata"])
    extra_userdata = {}
    extra_userdata["major"] = request.form["extra_userdata"]
    extra_userdata["facebook_id"] = session["id"]
    save_user_to_db(extra_userdata)
    session['major'] = extra_userdata["major"]
    return redirect("/")

@app.route("/logout")
def logout():
    pop_login_session()
    return redirect(url_for('index'))

def get_user_from_db(facebook_id):
    if not facebook_id:
        raise ValueError()
    users_found = models.User.objects(facebook_id=facebook_id)
    if len(users_found) == 1:
        return users_found[0]
    elif len(users_found) == 0:
        return None
    else:
        raise Exception('Database Integrity Error')

def save_user_to_db(user_data):
    users_found = models.User.objects(facebook_id=user_data['facebook_id'])
    if users_found:
        update_kwargs = {}
        for k,v in user_data.iteritems():
            update_key = 'set__%s' % k
            update_kwargs[update_key] = v
        #update_kwargs['upsert'] = True
        users_found.update(**update_kwargs)
    else:
        user = models.User()
        for k,v in user_data.iteritems():
            user[k] = v
        user.save()

# launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
