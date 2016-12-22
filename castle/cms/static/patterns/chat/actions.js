define([], function() {

  var RECEIVE_MESSAGE = 'RECEIVE_MESSAGE';
  var SET_ROOM = 'SET_ROOM';
  var ADD_MESSAGE = 'ADD_MESSAGE';
  var ADD_ROOM = 'ADD_ROOM';

  return {
    receiveMessage: function(message) {
      return {type: RECEIVE_MESSAGE, message: message};
    },
    setRoom: function(room) {
      return {type: SET_ROOM, room: room};
    },
    addRoom: function(room) {
      return {type: ADD_ROOM, room:room };
    },
    RECEIVE_MESSAGE: RECEIVE_MESSAGE,
    SET_ROOM: SET_ROOM,
    ADD_ROOM: ADD_ROOM
  };

});
