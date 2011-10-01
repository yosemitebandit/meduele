from twilio.rest import TwilioRestClient

account = "AXXXXXXXXXXXXXXXXX"
token = "YYYYYYYYYYYYYYYYYY"

client = TwilioRestClient(account, token)
call = client.calls.create( to="3093609866",
                            from_="3093609866", 
                            url="http://twilio.nfshost.com/med/hello-client-twiml.php")
print call.length
print call.sid