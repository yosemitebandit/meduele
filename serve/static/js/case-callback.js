var phoneNum = 3093609866;
var js_token = "{{ token }}";

try {
    Twilio.Device.setup(js_token);
} catch (err) {
    console.log("Adobe Flash is required to use Twilio Client.");
}

Twilio.Device.ready(function (device) {
    $("#log").text("Ready");
});

Twilio.Device.error(function (error) {
    $("#log").text("Error: " + error.message);
});

Twilio.Device.connect(function (conn) {
    $("#log").text("Successfully established call");
});

Twilio.Device.disconnect(function (conn) {
    $("#log").text("Call ended");
});

Twilio.Device.incoming(function (conn) {
    $("#log").text("Incoming connection from " + conn.parameters.From);
    // accept the incoming connection and start two-way audio
    conn.accept();
});

Twilio.Device.presence(function (pres) {
    if (pres.available) {
        // create an item for the client that became available
        $("<li>", {id: pres.from, text: pres.from}).click(function () {
            $("#number").val(pres.from);
            call();
        }).prependTo("#people");
    }
    else {
        // find the item by client name and remove it
        $("#" + pres.from).remove();
    }
});

function call() {
    params = {"PhoneNumber": phoneNum };
    Twilio.Device.connect(params);
    $("#call_button").text("Hang up");
    $("#call_button").attr('class', 'btn large danger call');
    $("#call_button").attr('onclick', '').click(function() { hangup(); });
}

function hangup() {
    Twilio.Device.disconnectAll();
    $("#call_button").text("Call");
    $("#call_button").attr('class', 'btn large primary call');
    $("#call_button").attr('onclick', '').click(function() { call(); });
}

