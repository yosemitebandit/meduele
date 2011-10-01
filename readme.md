## meduele
takes incoming calls, lets people respond with help in an asynch fashion

Patrick thinks this is awesome!


### high-level data types
```json
    volunteer {
      email address
      password stuff
      username
      bio
      picture
    }

    comment {
      author
      body
      timestamp
      patient_id
    }

    patient {
      patient_id 
      phone_number
    }

    incoming_call {
      patient_id
      internal_id
      timestamp
      twilio_link
      been_heard
      who_heard
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
    $ virtualenv --python=/path/to/python/bin --no-site-packages ~/virtualenvs/meduele-lib
    $ pip install -E ~/virtualenvs/meduele-lib flask-bcrypt
    $ pip install -E ~/virtualenvs/meduele-lib pymongo
  
go-time
    $ export MEDUELE_SETTINGS=/path/to/conf/meduele_settings.py
    $ /path/to/virtualenv/python /path/to/meduele/serve/meduele_server.py

