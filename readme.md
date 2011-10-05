## meduele
takes incoming calls, lets people respond with help in an asynch fashion.  650 262 5300

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
      comments: [{
        author, body, timestamp
      }]
    }

    cases {
      caseName
      callSID
      timestamp
      formattedTimestamp
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

    $ git add readme.md
    $ git commit -m 'some message'
    $ git pull

you may have to resolve conflicts at this point -- ask around if things looks weird

    $ git push


## testing and dependencies
here are some steps to run this whole project locally -- mongodb and several python packages are required.  this will
assume you're running a unix setup (sorry PYe).

1. install mongodb
   - you may want to use something like homebrew: https://github.com/mxcl/homebrew/wiki/installation
   - the download page: http://www.mongodb.org/downloads
   - once mongo is installed, the database server will likely start automatically.  You can check that it is running with:
    ```
    $ ps aux | grep mongod
    ```

   - if you need to start the server, this should start it running the background:
    ```
    $ mkdir -p /data/db
    $ sudo mongod --fork --logpath /var/log/mongodb.log --logappend
    ```

2. install pip and virtualenv
   - pip is a python package manager, it makes it very easy to install python libraries
   - virtualenv lets you set up isolated projects that have their own python package installations.  This is sometimes
     preferrable to installing packages system-wide as the latter can result in dependency conflicts.
      - note that virtualenv isn't required, just recommended since it can prevent some annoying situations
      - great intro article here: http://www.mahdiyusuf.com/post/5282169518/beginners-guide-easy-install-pip-and-virtualenv
   - so to get pip follow this guide: http://www.pip-installer.org/en/latest/installing.html
   - then to install virtualenv:
    ``` 
    $ sudo pip install -U virtualenv
    ```

3. create a virtualenv to hold all the dependencies for this project.  One pattern is to create a directory at
   ```~/virtualenvs/``` to hold virtualenvs for all your future projects.  A virtualenv is literally a directory inside
this dir; I typically append a "-lib" to the name of my main project.  Setting the --python flag is only needed if
you want this virtualenv to run a specific flavor of python.  The --no-site-packages makes a virtualenv with (almost) no
packages, as if your computer was brand new.
    ```
    $ mkdir -p ~/virtualenvs/meduele-lib
    $ virtualenv --python=/path/to/python/bin --no-site-packages ~/virtualenvs/meduele-lib
    ```

4. install the python packages into the virtualenv.  We're taking a tiny shorcut by specifying flask-bcrypt: pip will go out
   and install things like Flask and Jinja automatically as they are dependencies for the flask-bcypt package.
    ```
    $ pip install -E ~/virtualenvs/meduele-lib flask-bcrypt
    $ pip install -E ~/virtualenvs/meduele-lib pymongo
    $ pip install -E ~/virtualenvs/meduele-lib twilio
    ```

5. get a copy of the meduele project with git.  inside the meduele folder is another folder called meduele.  This contains a small package that gets installed like another python dependency.  It is at the moment just a series of functions built around handling mongo interactions.  Every time you edit a file in this package you will have to reinstall the meduele package with teh third command below:
    ```
    $ cd ~
    $ git clone git@github.com:yosemitebandit/meduele.git 
    $ pip install -E ~/virtualenvs/meduele-lib -e ~/meduele
    ```

6. the meduele project uses a small config file to initialize things and authenticate to other services like mongodb and
   twilio.  A sample config is inside the project at ```conf/meduele_settings.py```  You will want to make a copy of
this config somewhere *outside* of the project directory.  We will be adding sensitive info into the config that should
never be committed to source control.  We will also need to tell the meduele project where this real version of the
config file is; we do so by setting the ```MEDUELE_SETTINGS``` environmental variable.  We also want to put this env-var
setting into /etc/profile so the var gets set every time the shell starts up.  here's the whole process:
    ```
    $ cd ~/meduele/serve
    $ mkdir ~/conf
    $ cp ~/meduele/conf/meduele_settings_sample.py ~/conf/meduele_settings.py
    $ export MEDUELE_SETTINGS=~/conf/meduele_settings.py
    $ sudo echo export MEDUELE_SETTINGS=~/conf/meduele_settings.py >> /etc/profile
    ```

7. edit the ```~/conf/meduele_settings.py``` file to have the appropriate settings.  You will probably want to set
   ```DEBUG``` to be true so that the flask app is more responsive in your test environment.  You will also want to
change the initial user paramters -- this user will be injected into the database as the first account

8. initialize the database with the first user and some test content.  This is done by two functions within ```meduele_server.py```
    ```
    $ cd ~/meduele/serve
    $ ~/virtualenvs/meduele-lib/bin/python
    >> from meduele_server import init_admin, init_test_values
    >> init_admin()
    >> init_test_values()
    ```

8. finally we can start the test server.  Once it's started, visit the home page at the specified IP address and port.
    ```
    $ ~/virtualenvs/meduele-lib/bin/python ~/meduele/serve/meduele_server.py
    ```

 
### go-time

    $ export MEDUELE_SETTINGS=/path/to/conf/meduele_settings.py
    $ pip install -E /path/to/virtualenvs/meduele-lib -e /path/to/meduele
    $ /path/to/virtualenv/python /path/to/meduele/serve/meduele_server.py

or, if you're on the server, use supervisord or the fabfile or..if you must, gunicorn

    $ /path/to/virtualenv/gunicorn -c /path/to/gunicorn/conf.py run:app


### using twilio-python for outgoing calls

http://readthedocs.org/docs/twilio-python/en/latest/
    
    $ pip install twilio


### would be nice to have
 - tz knowledge and recs about when to call someone back
 - way to mark transcription as close enough or needs attention of language expert
    - twilioTranscription, englishTranscription, nativeLanguageTranscription would all be good

### should-fix
 - failures in firefox; related to <audio> element? ..if so, I don't think this element is needed
