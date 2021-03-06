from flask import Flask
import os

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , minilog.py
# Load default config and override config from an environment variable
app.config.update(dict(
    # SQLALCHEMY_DATABASE_URI='postgresql://yourusername@localhost/minilog',
    SQLALCHEMY_DATABASE_URI='sqlite:////%s' % os.path.join(app.root_path, 'db/minilog.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='A0Zr98j/3yX R~XHH!jmN]LWX/,?RT',
    UPLOAD_FOLDER=os.path.join(app.root_path, 'static/uploads'),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    FACEBOOK={
        "app_id": "425051767841997", # change your app id
        "app_secret": "" # Change your secret
    }
))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config.from_envvar('MINILOG_SETTINGS', silent=True)
