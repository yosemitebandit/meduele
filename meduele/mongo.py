'''
mongo.py
manages db transactions
'''
import os
import time
from operator import itemgetter

import pymongo

class Mongo:
    def __init__(self, mongoConfig):
        self.mongoConfig = mongoConfig

        self.connection = pymongo.Connection(mongoConfig['host'], int(mongoConfig['port']))   # mongo mandates integer ports
        self.db = self.connection[mongoConfig['dbName']]


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


    def retrieve_comments_by_project(self, projectName):
        query = {'projectName': projectName}
        returnFields = {'_id': False, 'projectName': False}
        return list(self.db['comments'].find(query, returnFields))
        

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


    def insert_new_comment(self, projectName, body, emailAddress):
        ''' create new comment in the db tied to the project
        '''
        comment = {
            'projectName': projectName
            , 'body': body
            , 'author': emailAddress
            , 'timestamp': int(time.time())
        }
        result = self.db['comments'].insert(comment)
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
            , 'userName': user
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
