/* global define */

define([
  'jquery',
  'moment',
  'mockup-utils',
  'castle-url/libs/react/react',
  'castle-url/node_modules/redux/dist/redux',
  'castle-url/patterns/chat/actions'
], function($, moment, utils, R, redux, actions) {
  'use strict';

  var D = R.DOM;

  var timer = null;

  var initialState = {
    messages: {},
    messageIds: {},
    channels: {},
    activeRoom: null
  };

  return function(state, action) {
    if( state === undefined ) {
      return initialState;
    }

    if( action.type === actions.SET_ROOM ) {
      if( state.messages[action.room] === undefined ) {
        state.messages[action.room] = [];
      }

      utils.loading.show();
      $('#castle-chat-message-box').hide();

      timer = setTimeout(function() {
        $('#castle-chat-message-box').show().scrollTop(1000000);
        utils.loading.hide();
      }.bind(utils), 200);

      state.activeRoom = action.room;
    }

    if( action.type === actions.ADD_ROOM ) {
      if( action.room === undefined ) {
        return state;
      }

      state.channels[action.room._id] = action.room;
    }

    if( action.type === actions.RECEIVE_MESSAGE ) {

      if( state.messageIds[action.message.id] !== undefined ) {
        return state;
      }

      clearTimeout(timer);
      timer = setTimeout(function() {
        $('#castle-chat-message-box').show().scrollTop(1000000);
        utils.loading.hide();
      }.bind(utils), 200);

      var mess = action.message;
      var room = mess.fields.rid;
      var messages = state.messages[room] || [];
      var ids = state.messageIds;

      if( mess.fields.ts === undefined ) {
        return state;
      }
      var time = moment(mess.fields.ts.$date).fromNow();

      var message = {
        id: mess.id,
        text: mess.fields.msg,
        time: time,
        timestamp: mess.fields.ts.$date,
        user: mess.fields.u.username,
        userId: mess.fields.u._id,
        type: mess.fields.t
      };

      ids[mess.id] = true;
      state.messageIds = ids;

      messages.unshift(message);
      state.messages[room] = messages.sort(function(a,b) {
        return a.timestamp - b.timestamp;
      });
    }

    return state;
  };

});
