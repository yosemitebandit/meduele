# the flask application's debug level.  /must/ be set to False for production
DEBUG = False

# generate a secret key with os.urandom(24)
SECRET_KEY = 'immma secret'

# local testing parameters
APP_IP = '127.0.0.1'
APP_PORT = 8000

# points to your mongodb instance
MONGO_CONFIG = {
    'dbName': 'meduele'
    , 'host': 'localhost'
    , 'port': 27017
}

# when first start the app and initializing the database, this user will be inserted
INITIAL_USER = {
    'emailAddress': 'bruce@wayneindustries.com'
    , 'userName': 'thebat'
    , 'password': 'j0k3rsuck5'
}

# your twilio credentials and the app sid for running handling the Twilio Client interaction
TWILIO_ACCOUNT_SID = 'AC123'
TWILIO_AUTH_TOKEN = 'abcd'
TWILIO_APP_SID = 'AP123'
