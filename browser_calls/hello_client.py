import os
from twilio.rest import TwilioRestClient
from twilio.util import TwilioCapability

settings_path = os.environ.get('MEDUELE_SETTINGS')
execfile(settings_path)

client_name = "jenny"

# client = TwilioRestClient(account, token)
# call = client.calls.create( to="9196225123",
#                             from_="3093609866", 
#                             url="http://twilio.nfshost.com/med/hello-client-twiml.php")

capability = TwilioCapability(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
capability.allow_client_outgoing(TWILIO_APP_SID)
capability.allow_client_incoming(client_name)
token = capability.generate()