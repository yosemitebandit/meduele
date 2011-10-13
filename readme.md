# meduele
MEDuele was built originally for the Cal Health Hackathon after hearing about the crowded free clinics in the South Bay.
The clinics offer their services to low-income patients but can only do so for a few hours each week.  The clinics also
have a high demand for translators as many of the incoming patients do not use English as their primary language.

The service we are prototyping allows patients to call in to a phone number and leave a message describing their ailments and questions.  They
are encouraged to speak in a language in which they are comfortable (ie, English is not mandatory).  After the call is
complete, a "case" is listed inside the MEDuele web app.  Verified volunteers can listen to the calls from their browser
and leave comments on the case itself.  Volunteers would be a mix of bilingual people that can aid in translation, 
medical professionals who can offer advice and, of course, medical professionals who also happen to be bilingual.  After listening to the original call and reviewing the case comments and any history from this caller, volunteers may then return the original client's call from the webapp using the magic of Twilio Client.

MEDuele is live at https://callmeduele.com and you can call our hotline at 650-262-5300

Check out the source and get involved: https://github.com/yosemitebandit/meduele


## setting up a local server
here are some steps to run this whole project locally -- mongodb and several python packages are required.  this will
assume you're running a unix setup (sorry PYe).

1. install mongodb
   - you may want to use something like homebrew: https://github.com/mxcl/homebrew/wiki/installation
      - one you have homebrew:
    ```
    $ brew install mongodb
    ```
   - or get mongo from the download page: http://www.mongodb.org/downloads
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

 - make sure you've reinstalled the latest meduele lib (step five above)
 - the MEDUELE_SETTINGS env var must point to a config (see steps six and seven in the setup process above)

    $ /path/to/virtualenv/python /path/to/meduele/serve/meduele_server.py

or, if you're on the server, use supervisord or the fabfile or..if you must, gunicorn

    $ /path/to/virtualenv/gunicorn -c /path/to/gunicorn/conf.py run:app


### twilio flow
when volunteers view a case, a call-back button is visible.  Here's what happens behind the scenes:

 1. in rendering that template, the twilio python library uses an Account ID and Auth Key (both bound to a paying
    account) as well as an App SID (bound to an App created under that account) to generate a capability token.
 2. this token is enabled for making outbound calls and is injected into the Twilio Client's javascript library
 3. the button is clicked and an outbound call begins, Twilio looks at the registered App's voice URL to determine what
    to do
 4. at the moment, that voice URL points to an endpoint at /twilio/outgoing_volunteer_call and the callSID of the
    original patient call is passed in as a URL parameter (somewhat confusing as this volunteer-initiated call has its
own CallSid)
 5. there were some issues with GETing vs POSTing to this URL (and other twilio endpoints) because of CSRF protection.
    There is currently a bit of a hack in place that doesn't perform a csrf check if 'twilio' is in the path.  This is a
problem only with profiles since all other names are auto-generated.
 6. the template rendered for the /twilio/outgoing_volunteer_call endpoint is passed a phone number based on the callSID
    parameter and the TwiML dial verb gets this phone number to start the call

see more: 
http://readthedocs.org/docs/twilio-python/en/latest/


### high-level data types
at the moment, this is not a perfect description of the actual data model.  But the test mongo db doesn't have it all
either; still working to reconcile the two.
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
      , 'comments': [_ids of comment objs]
      , 'lastLogin': int(time.time())
      , 'created': int(time.time())
      , 'adminRights': False
      , 'verified': False
    }
```

I don't think patients track comments like this..
```json 
    patient {
      patientName
      phoneNumber
      comments: [{
        author, body, timestamp
      }]
    }
```

```json
    comments {
      author
      timestamp
      body
    }
```

cases are also injected with transcription data
```json
    cases {
      caseName
      callSID
      timestamp
      formattedTimestamp
      url
      needsResolution
      duration
      phone number
      listeners [_ids of volunteers]
      comments [_ids of comment objs]
      responders [_ids of volunteers]
    }
```


### would be nice to have
 - tz knowledge and recs about when to call someone back
 - phone menu for incoming calls
 - way to mark transcription as close enough or needs attention of language expert
    - twilioTranscription, englishTranscription, nativeLanguageTranscription would all be good
 - make this a true hotline -- if a volunteer is online and 'available' route an incoming call to them rather than
   voicemail
 - method for marking cases as resolved
 - method to flag a call as 'in need of translation'


### should-fix
 - failures in firefox; related to <audio> element? ..if so, I don't think this element is needed


### other notes
 - visit anaestheseologists, cardiologists, nurses for advice
    - close to patients, very open to talking
    - early morning surgical centers 
 - translators are sometimes in short supply
 - but translators often needed in the hospital itself
 - a native speaker at your side can be very comforting
