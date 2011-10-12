#!/usr/bin/env python
'''
initialize.py
when the project is first setup, this can insert an admin user
separately, this can also inject some fake data
'''
import time

import flask
from flaskext.bcrypt import bcrypt_init, generate_password_hash, check_password_hash
import meduele 

app = flask.Flask(__name__)
app.config.from_envvar('MEDUELE_SETTINGS')
bcrypt_init(app)
mongo = meduele.Mongo(app.config['MONGO_CONFIG'])


def init_admin():
    ''' adds a default admin to the database
    usage: 
        $ /path/to/virtualenv/bin/python
        >> from initialize import init_admin
        >> init_admin()
        inserting "thebat"
    '''
    initial_user = app.config['INITIAL_USER']

    # make sure the values are unique
    query = {'emailAddress': initial_user['emailAddress']}
    emails = list(mongo.db['users'].find(query))

    query = {'userName': initial_user['userName']}
    names = list(mongo.db['users'].find(query))

    if emails:
        print 'failed, email exists'
    elif names:
        print 'failed, username exists'
    else:
        print 'inserting "%s"' % initial_user['userName']
        salt = mongo._create_random_string(34)

        volunteer = {
                'userName': initial_user['userName'] 
                , 'emailAddress': initial_user['emailAddress'] 
                , 'bio': '' 
                , 'languages': []
                , 'picture': None
                , 'salt': salt
                , 'passwordHash': generate_password_hash(initial_user['password'] + salt)
                , 'cases': [] 
                , 'lastLogin': int(time.time())
                , 'created': int(time.time())
                , 'adminRights': True
                , 'verified': True
                }

        mongo.db['users'].insert(volunteer)


def init_test_values():
    ''' adds some data to the db
    usage: 
        $ /path/to/virtualenv/bin/python
        >> from initialize import init_test_values
        >> init_test_values()
        inserting patient kuno13
    '''
    # inject some patients
    patientName = mongo._create_patient_name()
    patient = {
        'patientName': patientName
        , 'phoneNumber': '+0987612345'
    }
    print 'inserting patient %s' % patientName
    mongo.db['patients'].insert(patient)
    
    patientName = mongo._create_patient_name()
    patient = {
        'patientName': patientName
        , 'phoneNumber': '+1234567890'
    }
    print 'inserting patient %s' % patientName
    mongo.db['patients'].insert(patient)

    # inject some cases with the phone numbers above
    caseName = mongo._create_case_name()
    case = {
        'caseName': caseName
        , 'callSID': 'asdf123' 
        , 'timestamp': int(time.time())
        , 'formattedTimestamp': 'Monday, October 10, 2011 at 8:12pm'
        , 'url': 'http://google.com'
        , 'needsResolution': True
        , 'comments': []
        , 'duration': 45 
        , 'phoneNumber': '+0987612345'
        , 'responder': None
    }
    print 'inserting case %s' % caseName 
    mongo.db['cases'].insert(case)
    
    caseName = mongo._create_case_name()
    case = {
        'caseName': caseName
        , 'callSID': 'yuio456' 
        , 'timestamp': int(time.time()-10000)
        , 'formattedTimestamp': 'Monday, October 3, 2011 at 3:05pm'
        , 'url': 'http://nytimes.com'
        , 'needsResolution': False
        , 'comments': []
        , 'duration': 33
        , 'phoneNumber': '+1234567890'
        , 'responder': None
    }
    print 'inserting case %s' % caseName 
    mongo.db['cases'].insert(case)

