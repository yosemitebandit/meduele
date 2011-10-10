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
        return list(self.db['cases'].find(query).sort('timestamp', pymongo.DESCENDING).limit(responseLimit))
   

    def retrieve_cases(self, patientName):
        # first get the phone number from patients coll
        query = {'patientName': patientName}
        patient = list(self.db['patients'].find(query))[0]

        # now get cases based on phone number
        query = {'phoneNumber': patient['phoneNumber']}
        return list(self.db['cases'].find(query))


    def retrieve_case_by_caseName(self, caseName):
        query = {'caseName': caseName}
        return list(self.db['cases'].find(query))[0]


    def retrieve_users(self, **kwargs):
        ''' return users based on ..something
        '''
        emailAddress = kwargs.pop('emailAddress', None)
        userName = kwargs.pop('userName', None)

        if emailAddress:
            query = {'emailAddress': emailAddress}
        elif userName:
            query = {'userName': userName}
        else:
            query = {}
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

    
    #def compile_history_by_case(self, caseName):
        ''' return comments and calls linked to this case name, sorted by time
        '''
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
        '''

    
    def retrieve_open_cases(self, responseNumberLimit):
        ''' get three of the oldest calls that have not been marked resolved 
        '''
        query = {'needsResolution': True}
        returnFields = {'_id': False}
        return list(self.db['calls'].find(query, returnFields).sort('timestamp', pymongo.DESCENDING).limit(responseNumberLimit))


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
        ''' handles incoming calls from twilio
        generates new case (ie call) and creates a new patient if we've never seen this number before
        '''
        query = {'phoneNumber': incomingNumber}
        patient = list(self.db['patients'].find(query))
        if not patient:    # first-time caller; patient-gen
            patient = {'patientName': self._create_patient_name(), 'phoneNumber': incomingNumber}
            self.db['patients'].insert(patient)
        
        # save a formatted timestamp
        tzCorrection = 7   # eh, should really adjust for caller's timezone
        date = time.strftime('%A, %B %d, %Y', time.localtime(timestamp - tzCorrection*60*60))
        hours = int(time.strftime('%H', time.localtime(timestamp - tzCorrection*60*60)))
        if hours > 12:
            suffix = 'pm'
            hours = hours - 12
        elif hours == 0:  # convert to 12am
            hours = 12 
            suffix = 'am'
        else:
            suffix = 'am'
        minutes = time.strftime('%M', time.localtime(timestamp - tzCorrection*60*60))

        case = {
            'caseName': self._create_case_name() 
            , 'callSID': callSID
            , 'timestamp': timestamp
            , 'formattedTimestamp': '%s at %d:%s%s' % (date, hours, minutes, suffix)
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
        
        
    def insert_comment(self, patientName, caseName, userName, body):
        ''' create new comment in the db 
        insert refs to this comment into the case and user collections
        '''
        comment = {
            'body': body
            , 'author': userName 
            , 'timestamp': int(time.time())
        }
        commentID = self.db['comments'].insert(comment)

        # push this comment ID into the relevant case and collection documents
        query = {'caseName': caseName}
        self.db['cases'].update(query, {'$push': {'comments': commentID}})
        
        query = {'userName': userName}
        self.db['users'].update(query, {'$push': {'comments': commentID}})

        #self.track_interaction(caseName, userName)
        return (True, 'comment created')


    def retrieve_latest_comments(self, commentIDs, **kwargs):
        ''' pull down all the comments that match specific mongo IDs
        return up to limit of them, sort by timestamp, most recent first
        '''
        limit = kwargs.pop('limit', 100)    # uh, maybe just pass None into pymongo limit and see

        if not commentIDs:
            return []
        else:
            query = []
            for commentID in commentIDs:
                query.append({'_id': commentID})
            return self.db['comments'].find({'$or': query}).limit(limit).sort('timestamp', pymongo.DESCENDING)


    def update_user(self, userName, bio, passwordHash, languages, verified, adminRights):
        ''' handles any edits to the user page
        userName and emailAddress are currently immutable, though presumably one of them could be changed..
        '''
        query = {'userName': userName}
        self.db['users'].update(query, {'$set': {
                                            'bio': bio
                                            , 'passwordHash': passwordHash
                                            , 'languages': languages
                                            , 'verified': verified
                                            , 'adminRights': adminRights}})
        return (True, 'user info updated!')


    def register_user(self, userName, emailAddress, salt, passwordHash, languages, bio, picture):
        ''' handles the web registration
        '''
        if not userName or not emailAddress or not salt or not passwordHash or not bio:
            return (False, 'you seem to be missing some info')

        query = {'emailAddress': emailAddress}
        returnFields = {'_id': True}
        if list(self.db['users'].find(query, returnFields)):
            return (False, 'the email address "%s" is already registered with us' % emailAddress)

        query = {'userName': userName}
        returnFields = {'_id': True}
        if list(self.db['users'].find(query, returnFields)):
            return (False, 'the username "%s" is already registered with us' % userName)

        volunteer = {
            'userName': userName
            , 'emailAddress': emailAddress
            , 'bio': bio
            , 'languages': languages
            , 'picture': picture
            , 'salt': salt
            , 'passwordHash': passwordHash
            , 'cases': [] 
            , 'lastLogin': int(time.time())
            , 'created': int(time.time())
            , 'adminRights': False
            , 'verified': False
        }

        self.db['users'].insert(volunteer)
        return (True, 'thanks for signing up, we\'ll work to verify you soon!')


    def update_last_login(self, emailAddress):
        ''' updates the last-login field with the current time
        '''
        query = {'emailAddress': emailAddress}
        self.db['users'].update(query, {'$set': {'lastLogin': int(time.time())}})

    
    def _create_patient_name(self):
        ''' creates a cutesy identifier; moons and bikes for now
        '''
        eligible = [
            'phobos', 'io', 'europa', 'callisto', 'thebe', 'metis', 'themisto', 'tethys', 'titan', 'janus', 'calypso', 'prometheus', 'oberon'
            , 'alcyon', 'avanti', 'brennabor', 'brunswick', 'corima', 'dorel', 'ibis', 'kona', 'novara', 'rover', 'serotta', 'somec', 'zigo'
        ]
        while(True):
            # create a name like somec9, see if it already exists, save if not, woo efficiency
            proposedName = eligible[int(random.random()*len(eligible))] + str(int(random.random()*100) + 1)
            
            query = {'patientName': proposedName}
            returnFields = {'_id': True}
            if not list(self.db['patients'].find(query, returnFields).limit(1)):
                break

        return proposedName

    
    def _create_case_name(self):
        ''' creates a cutesy identifier; garden plants for now
        '''
        eligible = [
            'abelia', 'adenia', 'andira', 'cassina', 'duvalia', 'eucomis', 'ficus', 'ginko', 'hovea', 'inula', 'itea'
            , 'inula', 'kalmia', 'luma', 'maclura', 'melia', 'morina', 'orixa', 'parodia', 'selago', 'telekia'
        ]
        while(True):
            # create a name like somec9, see if it already exists, save if not, woo efficiency
            proposedName = eligible[int(random.random()*len(eligible))] + str(int(random.random()*100) + 1)
            
            query = {'caseName': proposedName}
            returnFields = {'_id': True}
            if not list(self.db['cases'].find(query, returnFields).limit(1)):
                break

        return proposedName


    def _create_random_string(self, length):
        # technique from: http://stackoverflow.com/questions/2898685/hashing-in-sha512-using-a-salt-python/2899137#2899137
        return ''.join(map(lambda x: './0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'[ord(x)%64], os.urandom(length)))
