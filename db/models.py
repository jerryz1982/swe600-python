import datetime
from flask import Flask
from flask.ext.mongoengine import MongoEngine
from mongoengine import connect

DB_NAME = 'facebook'
DB_USERNAME = 'swe600'
DB_PASSWORD = 'swe600'
DB_HOST_ADDRESS = 'ds061385.mlab.com:61385/facebook'
app = Flask(__name__)
app.config.update(
    DEBUG = True,
)
app.config["SECRET_KEY"] = 'swe600'
app.config["MONGODB_DB"] = DB_NAME
connect(DB_NAME, host='mongodb://' + DB_USERNAME + ':' + DB_PASSWORD + '@' + DB_HOST_ADDRESS)
db = MongoEngine(app)


class User(db.DynamicDocument):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    id = db.IntField(primary_key=True, required=True, unique=True)
    name = db.StringField(max_length=255, required=True)
    first_name = db.StringField(max_length=255, required=True)
    last_name = db.StringField(max_length=255, required=True)
    email = db.StringField(max_length=255, required=True)
    gender = db.StringField(max_length=255, required=True)
    friends_count = db.IntField(required=True)
    timezone = db.IntField(required=True)

    def __unicode__(self):
        return self.name

    meta = {
        'indexes' : ['-created_at', 'facebook_id'],
        'ordering' : ['-created_at']
    }
