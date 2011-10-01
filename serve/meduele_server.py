#!/usr/bin/env python
'''
meduele_server.py
'''
import os
import time

import flask
from flaskext.bcrypt import bcrypt_init, generate_password_hash, check_password_hash
import meduele 

app = flask.Flask(__name__)
app.config.from_envvar('MEDUELE_SETTINGS')
bcrypt_init(app)
mongo = meduele.Mongo(app.config['MONGO_CONFIG'])


@app.route('/cases', methods=['GET'])
@app.route('/cases/<caseName>', methods=['GET'])
@app.route('/cases/<caseName>/<action>', methods=['GET', 'POST'])
def show_cases(caseName=None, action=None):
    if 'logged_in' not in flask.session or not flask.session['logged_in']:  # not defined or is false
        return flask.redirect(flask.url_for('login'))

    if action == 'edit':
        if flask.request.method == 'GET':
            case = mongo.retrieve_cases_by_user(flask.session['emailAddress'], caseName)[0]
            return flask.render_template('edit_case.html', case=case)

        if flask.request.method == 'POST':
            (success, message) = mongo.update_case_info(
                                    caseName
                                    , flask.request.form['client']
                                    , flask.request.form['description']
                                    , flask.session['emailAddress'])
            if not success:
                #!
                case = {'description': flask.request.form['description'], 'client': flask.request.form['client'], 'name': caseName}
                return flask.render_template('show_cases.html', cases=[case])
            else:
                flask.flash('case %s updated, hooray!' % caseName)
                return flask.redirect(flask.url_for('show_cases', caseName=caseName))

    elif action == 'add_comment' and flask.request.method == 'POST':
        (success, message) = mongo.insert_new_comment(
                                caseName
                                , flask.request.form['body']
                                , flask.session['emailAddress'])
        if not success:
            flask.flash('comment not saved, sorry!')
        else:
            flask.flash('comment saved, wee!')
        return flask.redirect(flask.url_for('show_cases', caseName=caseName))

    elif action == 'add_case' and flask.request.method == 'POST':
        if not flask.session['adminRights']:
            flask.abort(400)   # or whatever forbidden is
        (success, caseName) = mongo.insert_new_case(
                                flask.request.form['caseName']
                                , flask.request.form['client']
                                , flask.request.form['description']
                                , flask.session['emailAddress']) 
        if not success:
            flask.flash('case not saved, apologies!')
        else:
            flask.flash('case %s created, hooray!' % flask.request.form['caseName'])
        return flask.redirect(flask.url_for('show_cases', caseName=caseName))

    elif not action and flask.request.method == 'GET':
        if caseName:   # specific case name specified
            # retrieve all the comments and calls for a case
            history = mongo.compile_history_by_case(caseName)
            acceptComments = True
        else:   # generic request to /cases
            # retrieve the lastest audio interaction
            history = mongo.retrieve_open_cases(4)
            acceptComments = False
        return flask.render_template('show_cases.html'
                                    , caseName=caseName
                                    , history=history
                                    , acceptComments=acceptComments)
    else:
        flask.abort(405)


@app.route('/users', methods=['GET'])
@app.route('/users/<userName>', methods=['GET'])
@app.route('/users/<userName>/<action>', methods=['GET', 'POST'])
def show_users(userName=None, action=None):
    if 'logged_in' not in flask.session or not flask.session['logged_in']:  # not defined or is false
        return flask.redirect(flask.url_for('login'))

    if action == 'edit':
        if flask.request.method == 'GET':
            user = mongo.retrieve_user(emailAddress=emailAddress)[0]
            cases = mongo.retrieve_cases_by_user(flask.session['emailAddress'], None)
            return flask.render_template('edit_user.html', user=user, cases=cases)

        if flask.request.method == 'POST':
            _salt = mongo._create_random_string(34)
            _hash = generate_password_hash(flask.request.form['password'] + _salt)
            _adminRights = True if flask.request.form['adminRights'] == 'True' else False
            (success, message) = mongo.update_user_info(
                                    emailAddress
                                    , _salt
                                    , _hash
                                    , _adminRights
                                    , flask.request.form.getlist('cases'))
            if not success:
                flask.flash('user %s not updated, sorry' % emailAddress)
            else:
                flask.flash('user %s updated, hooray!' % emailAddress)
            return flask.redirect(flask.url_for('show_users', emailAddress=emailAddress))

    elif action == 'add_user' and flask.request.method == 'POST':
        if not flask.session['adminRights']:
            flask.abort(400)   # or whatever forbidden is
        _salt = mongo._create_random_string(34)
        _hash = generate_password_hash(flask.request.form['password'] + _salt)
        _adminRights = True if flask.request.form['adminRights'] == 'True' else False
        (success, message) = mongo.insert_new_user(
                                flask.request.form['emailAddress']
                                , _salt
                                , _hash
                                , _adminRights
                                , flask.request.form.getlist('cases'))
        if not success:
            flask.flash('user not saved, apologies!')
        else:
            flask.flash('user %s created, hooray!' % flask.request.form['emailAddress'])
        return flask.redirect(flask.url_for('show_users'))

    elif not action and flask.request.method == 'GET':
        if not userName:
            users = mongo.retrieve_user(userName='*')
        else:
            users = mongo.retrieve_user(userName=userName)

        if len(users) == 1:
            acceptNewUser = False
        else:
            if flask.session['adminRights']:
                acceptNewUser = True
            else:
                acceptNewUser = False

        return flask.render_template('show_users.html'
                                    , users=users
                                    , cases=cases
                                    , acceptNewUser=acceptNewUser)
    else:
        flask.abort(405)


@app.route('/twilio/incoming_handler.xml', methods=['GET'])
def twilio_incoming():
    return flask.render_template('twilio_incoming.xml')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if flask.request.method == 'POST':
        user = mongo.retrieve_user(emailAddress=flask.request.form['emailAddress'])[0]

        if not user or not check_password_hash(user['password_hash'], flask.request.form['password'] + user['salt']):
            error = 'login error, bad username/password combination.'
        elif ('verified' not in user.keys() or not user['verified']) and not user['adminRights']:
            error = 'sorry, you have not yet been verified.'
        else:
            mongo.update_last_login(flask.request.form['emailAddress'])   # updates last-login timestamp

            flask.session['logged_in'] = True
            flask.session['emailAddress'] = flask.request.form['emailAddress']
            flask.session['adminRights'] = user['adminRights']
            flask.session['apiID'] = user['apiID']
            flask.session['apiKey'] = user['apiKey']
            flask.flash('you logged in, nice!')
            return flask.redirect(flask.url_for('show_cases'))
        
    return flask.render_template('login.html', error=error)


@app.route('/logout')
def logout():
    flask.session.pop('logged_in', None)
    flask.session.pop('emailAddress', None)
    flask.flash('you logged out, adios')
    return flask.redirect(flask.url_for('show_home'))


@app.route('/')
def show_home():
    if 'logged_in' in flask.session:
        return flask.redirect(flask.url_for('show_cases'))
    return flask.render_template('show_home.html')


def init():
    ''' adds a default admin to the case
    usage: 
        $ /path/to/virtualenv/bin/python
        >> from airship_server import init
        >> init()
        user "bruce@wayneindustries.com" created with specified password
    '''
    userName = 'batman'
    emailAddress = app.config['INIT_EMAIL']
    password = app.config['INIT_PASSWORD']
    bio = 'hard childhood'
    picture = None

    if mongo.retrieve_user(userName=userName):
        print 'failed, username "%s" exists' % username
    if mongo.retrieve_user(emailAddress=emailAddress):
        print 'failed, emailAddres "%s" exists' % emailAddress 
    else:
        _salt = mongo._create_random_string(34)
        _hash = generate_password_hash(password + _salt)
        _adminRights = True
        (success, message) = mongo.insert_new_user(
                                username 
                                , emailAddress
                                , bio
                                , picture
                                , _salt
                                , _hash
                                , _adminRights
                                , [])
        if success:
            print 'user "%s" created with specified password' % username
        else:
            print 'user creation failed, sorry.'

    (success, message) = mongo.insert_comment(
                            emailAddress
                            , 'what a lovely case'
                            , int(time.time())
                            , 'Red Badger')
    if success:
        print 'comment created'

    (success, message) = mongo.insert_patient(
                            'Red Badger'
                            , '4568123421')

    if success:
        print 'patient created'
'''
    (success, message) = mongo.insert_incoming_call(
                            'Red Badger'
                            , 'internalABC'
                            , int(time.time() - 100)
                            , 'twiliolink'
                            , '

    incoming_call {
      patient_id
      internal_id
      timestamp
      twilio_link
      been_heard
      who_heard
    }
'''

if __name__ == '__main__':
    app.run(host=app.config['APP_IP'], port=app.config['APP_PORT'])

