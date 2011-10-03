## meduele
takes incoming calls, lets people respond with help in an asynch fashion.  650 262 5300

Patrick thinks this is awesome!


### high-level data types
```json
      volunteer = {
            'userName': userName
            , 'emailAddress': emailAddress
            , 'bio': bio
            , 'languages': languages
            , 'picture': picture
            , 'salt': salt
            , 'password_hash': passwordHash
            , 'cases': [] 
            , 'lastLogin': int(time.time())
            , 'created': int(time.time())
            , 'adminRights': False
            , 'verified': False
        }
 
    patient {
      patientName
      phoneNumber
    }

    cases {
      caseName
      callSID
      timestamp
      url
      needsResolution
      duration
      phone number
      who_heard
      comments: [{
        author
        body
        timestamp
      }]
    }
```

### git workflow
'$' means type this in the terminal (but omit the actual '$' sign)

    $ git add readme.md
    $ git commit -m 'some message'
    $ git pull

[[ resolve conflicts -- ask around if it looks weird ]]

    $ git push

### testing 
  
create a virtualenv and install the dependencies:

    $ mkdir -p ~/virtualenvs/meduele-lib
    $ virtualenv --python=/path/to/python/bin --no-site-packages /path/to/virtualenvs/meduele-lib
    $ pip install -E /path/to/virtualenvs/meduele-lib flask-bcrypt
    $ pip install -E /path/to/virtualenvs/meduele-lib pymongo
    $ pip install -E /path/to/virtualenvs/meduele-lib -e meduele/
  
go-time

    $ export MEDUELE_SETTINGS=/path/to/conf/meduele_settings.py
    $ pip install -E /path/to/virtualenvs/meduele-lib -e /path/to/meduele
    $ /path/to/virtualenv/python /path/to/meduele/serve/meduele_server.py

or, if you're on the server, use supervisord or the fabfile or..if you must, gunicorn

    $ /path/to/virtualenv/gunicorn -c /path/to/gunicorn/conf.py run:app

### using twilio-python for outgoing calls

http://readthedocs.org/docs/twilio-python/en/latest/
    
    $ pip install twilio
    
