#!/usr/bin/env python
'''
meduele_server.py
'''
import time

from twilio.rest import TwilioRestClient
from twilio.util import TwilioCapability
import flask
from flaskext.bcrypt import bcrypt_init, generate_password_hash, check_password_hash
import meduele 

app = flask.Flask(__name__)
app.config.from_envvar('MEDUELE_SETTINGS')
bcrypt_init(app)
mongo = meduele.Mongo(app.config['MONGO_CONFIG'])


@app.route('/patients/<patientName>', methods=['GET'])
def show_patient(patientName):
    if 'logged_in' not in flask.session or not flask.session['logged_in']:  # not defined or is false
        return flask.redirect(flask.url_for('login'))
    
    if not flask.session['verified']:
        return flask.render_template('show_patients.html', notVerified=True)

    cases = mongo.retrieve_cases(patientName)
    resolved = []
    unresolved = []
    for case in cases:
        if 'needsResolution' in case.keys() and case['needsResolution']:
            unresolved.append(case)
        else:
            resolved.append(case)

    return flask.render_template('show_patients.html', patientName=patientName, unresolved=unresolved, resolved=resolved)


@app.route('/patients/<patientName>/cases/<caseName>', methods=['GET'])
def show_case(patientName, caseName):
    if 'logged_in' not in flask.session or not flask.session['logged_in']:  # not defined or is false
        return flask.redirect(flask.url_for('login'))
    
    if not flask.session['verified']:
        return flask.render_template('show_case.html', notVerified=True)

    case = mongo.retrieve_case_by_caseName(caseName)
    
    client_name = 'will'
    capability = TwilioCapability(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
    capability.allow_client_outgoing(app.config['TWILIO_APP_SID'])
    token = capability.generate()

    url = case['url']
    protocol = url.split(':')
    case['url'] = protocol[0] + 's:' + protocol[1]
    return flask.render_template('show_case.html', client=client_name, token=token, patientName=patientName, case=case)


@app.route('/cases', methods=['GET'])
def show_new_cases():
    if 'logged_in' not in flask.session or not flask.session['logged_in']:  # not defined or is false
        return flask.redirect(flask.url_for('login'))

    if not flask.session['verified']:
        return flask.render_template('new_cases.html', notVerified=True)

    cases = mongo.retrieve_unresolved_cases(6)
    _cases = []
    for case in cases:
        patientName = mongo.find_patientName_by_phoneNumber(case['phoneNumber'])
        case['patientName'] = patientName
        _cases.append(case)

    return flask.render_template('new_cases.html', cases=_cases)


'''
session setting/destroying
'''
@app.route('/volunteer', methods=['GET', 'POST'])
def register():
    if flask.request.method == 'GET':
        if 'logged_in' in flask.session and flask.session['logged_in']:
            return flask.render_template('register.html', alreadyRegistered=True)
        else:
            return flask.render_template('register.html')


    if flask.request.method == 'POST':
        if not flask.request.form['userName'] \
                and not flask.request.form['emailAddress'] \
                and not flask.request.form['password'] \
                and not flask.request.form['retypePassword'] \
                and not flask.request.form['bio']:
            return flask.render_template('register.html', error='we\'re missing some info')

        if flask.request.form['password'] != flask.request.form['retypePassword']:
            return flask.render_template('register.html', error='passwords do not match')

        if len(flask.request.form['password']) < 6:
            return flask.render_template('register.html', error='passwords must be at least six characters')
        salt = mongo._create_random_string(34)
        passwordHash = generate_password_hash(flask.request.form['password'] + salt)

        # def register_user(self, userName, emailAddress, password, retypePassword, languages, bio, picture):
        (success, message) = mongo.register_user(
                                flask.request.form['userName']
                                , flask.request.form['emailAddress']
                                , salt
                                , passwordHash
                                , flask.request.form.getlist('languages')
                                , flask.request.form['bio']
                                , None)   # picture
        if success:
            # log them in 
            flask.session['logged_in'] = True
            flask.session['emailAddress'] = flask.request.form['emailAddress']
            flask.session['userName'] = flask.request.form['userName']
            flask.session['adminRights'] = False
            flask.session['verified'] = False

            return flask.redirect(flask.url_for('show_new_cases'))
        
        else:
            return flask.render_template('register.html', error=message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return flask.render_template('login.html')

    else:
        error = None
        user = mongo.retrieve_users(userName = flask.request.form['userName'])
        if user:
            user = user[0]
        else:  # userName not found
            error = 'That\'s a bad username/password combination'
            return flask.render_template('login.html', error=error)

        if not check_password_hash(user['passwordHash'], flask.request.form['password'] + user['salt']):
            error = 'That\'s a bad username/password combination'
            return flask.render_template('login.html', error=error)

        mongo.update_last_login(user['emailAddress'])   # updates last-login timestamp

        flask.session['logged_in'] = True
        flask.session['emailAddress'] = user['emailAddress']
        flask.session['userName'] = user['userName']
        flask.session['adminRights'] = user['adminRights']
        flask.session['verified'] = user['verified']
        return flask.redirect(flask.url_for('show_new_cases'))


@app.route('/logout', methods=['POST'])
def logout():
    flask.session.pop('logged_in', None)
    flask.session.pop('emailAddress', None)
    flask.session.pop('userName', None)
    flask.session.pop('adminRights', None)
    flask.session.pop('verified', None)

    flask.flash('logged out!', category='success')
    return flask.redirect(flask.url_for('show_home'))


'''
basic routes
'''
@app.route('/')
def show_home():
    return flask.render_template('show_home.html')
    

@app.route('/about', methods=['GET'])
def show_about():
    return flask.render_template('show_about.html')


@app.route('/contact', methods=['GET'])
def show_contact():
    return flask.render_template('show_contact.html')


@app.route('/leaderboard', methods=['GET'])
def show_leaderboard():
    return flask.render_template('show_leaderboard.html')


'''
twilio handlers
'''
@app.route('/twilio/client', methods=['POST'])
def twilio_client():
    return flask.render_template('twilio_client.xml')
    

@app.route('/twilio/incoming_handler.xml', methods=['GET'])
def twilio_incoming():
    return flask.render_template('twilio_incoming.xml')


@app.route('/twilio/incoming_callback', methods=['POST'])
def twilio_incoming_callback():
    callSID = flask.request.form['CallSid']
    incomingNumber = flask.request.form['From']
    dialedNumber = flask.request.form['To']
    # http://www.twilio.com/docs/api/twiml/twilio_request#synchronous-request-parameters
    url = flask.request.form['RecordingUrl']
    duration = flask.request.form['RecordingDuration']
    
    # insert into db..
    mongo.insert_case(
            callSID
            , int(time.time())
            , url
            , True
            , duration
            , incomingNumber
            , None)
    # not sure what to return here..
    return flask.redirect(flask.url_for('show_home'))


@app.route('/twilio/transcription_callback', methods=['POST'])
def twilio_transcription_callback():
    callSID = flask.request.form['CallSid']
    # http://www.twilio.com/docs/api/twiml/twilio_request#synchronous-request-parameters
    transcriptionText = flask.request.form['TranscriptionText']
    transcriptionStatus = flask.request.form['TranscriptionStatus']
    transcriptionURL = flask.request.form['TranscriptionUrl']
    
    # insert into db..
    mongo.update_case(
            callSID
            , transcriptionText
            , transcriptionStatus 
            , transcriptionURL)

    # not sure what to return here..
    return flask.redirect(flask.url_for('show_home'))


@app.route('/test', methods=['GET'])
def show_test():
    # if 'logged_in' not in flask.session or not flask.session['logged_in']:  # not defined or is false
    #     return flask.redirect(flask.url_for('show_home'))
    # else:
        client_name = flask.session['userName']
        capability = TwilioCapability(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
        capability.allow_client_outgoing(app.config['TWILIO_APP_SID'])
        capability.allow_client_incoming(client_name)
        token = capability.generate()
        # client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # call = client.calls.create( to="9196225123",
        #                                    from_="3093609866", 
        #                                    url="http://twilio.nfshost.com/med/hello-client-twiml.php")
        # return flask.render_template('show_signup.html', error=error, client=client_name, token=token)
        return flask.render_template('show_test.html', token=token, client=client_name)


'''
db init
'''
def init():
    ''' adds a default admin to the database
    usage: 
        $ /path/to/virtualenv/bin/python
        >> from airship_server import init
        >> init()
        user "bruce@wayneindustries.com" created with specified password
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
        print 'inserting %s' % initial_user['userName']
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


if __name__ == '__main__':
    app.run(host=app.config['APP_IP'], port=app.config['APP_PORT'])

