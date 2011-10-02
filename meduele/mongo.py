'''
mongo.py
manages db transactions
'''
import os
import time
from operator import itemgetter
import random

import pymongo

class Mongo:
    def __init__(self, mongoConfig):
        self.mongoConfig = mongoConfig

        self.connection = pymongo.Connection(mongoConfig['host'], int(mongoConfig['port']))   # mongo mandates integer ports
        self.db = self.connection[mongoConfig['dbName']]


    def find_patientName_by_phoneNumber(self, phoneNumber):
        query = {'phoneNumber': phoneNumber}
        patients = list(self.db['patients'].find(query))[0]
        return patients['patientName']


    def retrieve_unresolved_cases(self, responseLimit):
        query = {'needsResolution': True}
        cases = list(self.db['cases'].find(query).sort('timestamp', pymongo.ASCENDING).limit(responseLimit))
        return cases 
   

    def retrieve_cases(self, patientName):
        # first get the phone number from patients coll
        query = {'patientName': patientName}
        patient = list(self.db['patients'].find(query))[0]

        # now get cases based on phone number
        query = {'phoneNumber': patient['phoneNumber']}
        cases = list(self.db['cases'].find(query))
        
        _cases = []
        for case in cases:
            case['timestamp'] = time.strftime('%a, %d %b %Y %H:%M', time.localtime(case['timestamp']))
            _cases.append(case)
        return _cases


    def retrieve_case_by_caseName(self, caseName):
        query = {'caseName': caseName}
        case = list(self.db['cases'].find(query))[0]
        return case


    def retrieve_user(self, **kwargs):
        emailAddress = kwargs.pop('emailAddress', None)
        userName = kwargs.pop('userName', None)
        ''' return user info based on a specified email address
        '''
        if emailAddress == '*':
            query = {}
        else:
            query = {'emailAddress': emailAddress}
        returnFields = {'_id': False}
        return list(self.db['users'].find(query, returnFields))


    def remove_user(self, emailAddress):
        ''' deletes user based on a specified email address
        '''
        query = {'emailAddress': emailAddress}
        returnFields = {'_id': False}
        self.db['users'].remove(query)
        # eh, mongo doesn't really reply..sigh
        return True

    
    def compile_history_by_case(self, caseName):
        ''' return comments and calls linked to this case name, sorted by time
        '''
        # get all the calls
        query = {'caseName': caseName}
        returnFields = {'_id': False}
        calls = list(self.db['calls'].find(query, returnFields).sort('timestamp', pymongo.DESCENDING).limit(10))

        # get all the comments; cheating a bit with the same query
        
        comments = list(self.db['comments'].find(query, returnFields).sort('timestamp', pymongo.DESCENDING).limit(10))

        # combine and sort by timestamp
        history = calls
        history.extend(comments)
        return sorted(history, key = itemgetter('timestamp'))

    
    def retrieve_open_cases(self, responseNumberLimit):
        ''' get three of the oldest calls that have not been marked resolved 
        '''
        query = {'needsResolution': True}
        returnFields = {'_id': False}
        return list(self.db['calls'].find(query, returnFields).sort('timestamp', pymongo.ASCENDING).limit(responseNumberLimit))


    def retrieve_cases_by_name(self, projectNames):
        if projectNames == '*':
            query = {}
        elif not projectNames:   # edge case, no cases assigned to a user; $or blows up if you don't handle it here
            return []
        else:
            names = []
            for projectName in projectNames:
                names.append({'name': projectName})
            query = {'$or': names}
        returnFields = {'_id': False, 'name': True, 'client': True, 'description': True}
        return list(self.db['cases'].find(query, returnFields))


    def insert_case(self, callSID, timestamp, url, needsResolution, duration, incomingNumber, responder):
        caseName = 'odelay' + str(int(random.random()*100000))
        
        query = {'phoneNumber': incomingNumber}
        patient = list(self.db['patients'].find(query))
        if not patient:    # first-time caller; patient-gen
            patientName = 'shakespeare' + str(int(random.random()*100000))
            patient = {'patientName': patientName, 'phoneNumber': incomingNumber}
            self.db['patients'].insert(patient)
        
        case = {
            'caseName': caseName
            , 'callSID': callSID
            , 'timestamp': timestamp
            , 'url': url
            , 'needsResolution': needsResolution
            , 'duration': duration
            , 'phoneNumber': incomingNumber
            , 'responder': responder
        }
        result = self.db['cases'].insert(case)

    
    def update_case(self, callSID, text, status, url):
        ''' inserts the transcription data into the case object
        '''
        if status == 'completed':
            query = {'callSID': callSID}
            self.db['cases'].update(query, {'$set': {'transcriptionText': text
                                                        , 'transcriptionStatus': status
                                                        , 'transcriptionURL': url}})


    def insert_new_project(self, projectName, client, description, emailAddress):
        ''' create new project in the db
        '''
        query = {'name': projectName}
        returnFields = {'_id': True}
        if list(self.db['cases'].find(query, returnFields)):
            return (False, 'project name exists')

        apiID = self._create_random_string(34)
        project = {
            'name': projectName
            , 'client': client
            , 'description': description
            , 'createdBy': emailAddress
            , 'createdAt': int(time.time())
            , 'apiID': apiID
            , 'apiKey': self._create_random_string(34)
        }
        result = self.db['cases'].insert(project)
        return (True, projectName)


    def track_interaction(self, caseName, userName):
        ''' make sure the volunteer's case list has this case
        '''
        user = self.retrieve_user(userName=userName)
        print user, caseName
        if user and caseName not in user['cases']:
            # eh..
            user['cases'] = user['cases'].append(caseName)
            query = {'caseName': caseName}
            self.db['users'].update(query, user)


    def insert_comment(self, userName, body, caseName, callSID):
        ''' create new comment in the db tied to the project
        also make sure this volunteer/patient interaction is tracked
        '''
        comment = {
            'caseName': caseName 
            , 'body': body
            , 'author': userName 
            , 'timestamp': int(time.time())
            , 'callSID': callSID
        }
        result = self.db['comments'].insert(comment)

        self.track_interaction(caseName, userName)
        return (True, 'comment created')

    
    def insert_new_patient(self, name, phoneNumber):
        ''' create a new patient if the phone number does not exist already
        '''
        query = {'phoneNumber': phoneNumber}
        returnFields = {'_id': True}
        if list(self.db['patients'].find(query, returnFields)):
            return (False, 'phone number exists')

        patient = {
            'phoneNumber': phoneNumber
            , 'name': name
        }
        result = self.db['patients'].insert(patient)
        return (True, 'patient created')


    def insert_new_user(self, userName, emailAddress, bio, picture, salt, passwordHash, adminRights, cases):
        ''' create a new user in the db if the user doesn't exist already
        '''
        query = {'emailAddress': emailAddress}
        returnFields = {'_id': True}
        if list(self.db['users'].find(query, returnFields)):
            return (False, 'user exists')

        user = {
            'emailAddress': emailAddress
            , 'userName': userName
            , 'bio': bio
            , 'picture': picture
            , 'salt': salt
            , 'password_hash': passwordHash
            , 'cases': cases
            , 'lastLogin': None
            , 'created': int(time.time())
            , 'adminRights': adminRights
        }
        result = self.db['users'].insert(user)
        return (True, 'An account for "%s" has been made' % emailAddress)

    
    def update_project_info(self, projectName, client, description, emailAddress):
        ''' updates the mutable project data
        '''
        query = {'name': projectName}
        self.db['cases'].update(query, {'$set': {'client': client
                                                    , 'description': description
                                                    , 'updatedAt': int(time.time())
                                                    , 'updatedBy': emailAddress}})
        return (True, 'project %s updated' % projectName)


    def update_last_login(self, emailAddress):
        ''' updates the last-login field with the current time
        '''
        query = {'emailAddress': emailAddress}
        self.db['users'].update(query, {'$set': {'lastLogin': int(time.time())}})


    def _create_random_string(self, length):
        # technique from: http://stackoverflow.com/questions/2898685/hashing-in-sha512-using-a-salt-python/2899137#2899137
        return ''.join(map(lambda x: './0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'[ord(x)%64], os.urandom(length)))
