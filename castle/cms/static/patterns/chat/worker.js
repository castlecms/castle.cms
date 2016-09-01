importScripts('../../asteroid.js');

var conn = null;
var port = null;
var time = null;
onconnect = function(e) {
    port = e.ports[0];
    time = Date.now().toString();

    port.onmessage = function(e) {
        switch( e.data.action ) {
            case 'init':
                init(e.data);
                break;
            case 'login':
                login(e.data);
                break;
            case 'logout':
                conn.logout();
                close();
                break;
            case 'sendMessage':
                sendMessage(e.data);
                break;
            case 'setActiveChannel':
                setActiveChannel(e.data.room);
                break;
        }
    };
};

var init = function(data) {
    var asteroid = Asteroid.createClass();
    var options = {
        endpoint: data.url
    };

    //Normally we'd put this in a try/catch, but we're letting
    //the main script handle the web workers errors
    conn = new asteroid(options);
};

var login = function(data) {

    conn.call('login', {
        cookie: data.token,
        user:{
            id: data.user,
            email: data.email
        }
    }).then(function() {
        conn.call('channelsList', '', 'public').then(function(channelInfo) {
            if( channelInfo.channels === undefined ) {
                return;
            }
            channelInfo.channels.forEach(function(item) {
                port.postMessage({'action': 'addChannel', 'room': item});
                conn.subscribe("messages", item._id);
            });

            setActiveChannel(channelInfo.channels[0]);

            conn.ddp.on("added", function(res) {
                port.postMessage({'action': 'addMessage', 'message': res});
            });
        });
    });
};

var setActiveChannel = function(room) {
    port.postMessage({'action': 'setRoom', 'room': room});
    conn.call("readMessages", room._id);
};

var sendMessage = function(data) {
    var room = data.rid;
    var msg = data.msg;

    conn.call('sendMessage', {rid: room, msg: msg}).then(function(res) {
      port.postMessage({'action': 'sentMessage', 'msg': res});
    });
};
