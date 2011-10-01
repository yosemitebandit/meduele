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
