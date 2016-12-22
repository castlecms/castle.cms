/* global define */

define([
  'jquery',
  'mockup-utils',
  'mockup-patterns-base',
  'castle-url/libs/react/react',
  'castle-url/node_modules/redux/dist/redux',
  'castle-url/patterns/chat/reducer',
  'castle-url/patterns/chat/actions'
], function($, utils, Base, R, redux, reducer, actions) {
  'use strict';

  var store = redux.createStore(reducer);
  var D = R.DOM;
  var sub = null;

  var timer = null;

  var getCookieValue = function(name) {
    var cookie = document.cookie;
    var parts = cookie.split(';');

    var sess_id = '';

    parts.forEach(function(item) {
      var splitValues = item.split('=');
      if( splitValues[0].replace(' ', '') === name ) {
        sess_id = splitValues[1].split('"').join("");
      }
    }.bind(name));

    return sess_id;
  };

  var chatComponent = R.createClass({
    clearTextBox: function() {
      var box = this.refs.messageBox.getDOMNode();
      box.value = '';
    },
    closeConnection: function() {
      //used by the toolbar to log out the user when the chat window is closed.
      this.state.worker.port.postMessage({'action': 'logout'});
    },
    cleanRoom: function(rid) {
      var room = this.state.channels[rid];

      room.alert = false;
      room.unread = 0;

      this.state.channels[rid] = room;

      var index = this.state.unreadChannels.indexOf(rid);
      if( index >= 0 ) {
        this.state.unreadChannels.splice(index, index+1);
      }
    },
    changeRoom: function(rid) {
      this.setLoading();
      store.dispatch(actions.setRoom(rid));
    },
    foulRoom: function(rid) {
      this.state.unreadChannels.push(rid);
    },
    componentDidMount: function() {
      if( !this.state.valid ) {
        return;
      }

      this.state.worker.port.postMessage({
        'action': 'login',
        'token':  this.props.token + getCookieValue('castle_session_id'),
        'email': this.props.email,
        'user': this.props.user
      });
    },
    componentWillMount: function() {
      if( !this.state.valid ) {
        return;
      }

      this.state.store.subscribe(function() {
        var state = this.state.store.getState();

        this.setState({
          'messages': state.messages,
          'activeRoom': state.activeRoom,
          'channels': state.channels
        });
      }.bind(this));

      this.state.worker.port.start();
      this.state.worker.port.postMessage({'action': 'init', 'url': this.props.url});
    },
    componentWillUnmount: function() {
      this.state.worker.port.postMessage({'action': 'logout'});
      //this.state.worker.port.terminate();
    },
    getInitialState: function() {
      var user = this.props.user;
      var email = this.props.email;

      if( user === '' || email === '' ) {
        return {
          'valid': false
        };
      }

      var worker = new SharedWorker('++plone++castle/patterns/chat/worker.js', 'rocketchat');
      worker = this.setWorkerBindings(worker);

      return {
        'userId': null,
        'worker': worker,
        'authToken': null,
        'channels': null,
        'store': store,
        'messages': null,
        'activeRoom': null,
        'valid': true,
        'handle': sub,
        'subbedChannels': {},
        'tokenStub': this.props.token,
        'unreadChannels': this.props.unreadChannels || [],
      };
    },
    sendMessage: function() {
      var message = this.refs.messageBox.getDOMNode().value;

      this.state.worker.port.postMessage({
        'action': 'sendMessage',
        'msg': message,
        'rid': this.state.activeRoom
      });

      this.clearTextBox();
    },
    setWorkerBindings: function(worker) {
      var that = this;

      if( worker === undefined ) {
        return worker;
      }

      worker.port.onmessage = function(e) {

        var action = e.data.action;

        switch(action) {
          case 'addChannel':
            store.dispatch(actions.addRoom(e.data.room));
            break;
          case 'addMessage':
            store.dispatch(actions.receiveMessage(e.data.message));
            break;
          case 'setRoom':
            that.changeRoom(e.data.room._id);
            that.cleanRoom(e.data.room._id);
            break;
          case 'sentMessage':
            store.dispatch(actions.addMessage(e.data.msg));
            break;
        }
      };

      worker.port.onerror = function(e){
        debugger;
      };

      return worker;
    },
    setActiveChannel: function(name) {
      if( this.state.activeRoom === name ) {
        return;
      }
      this.setLoading();
      this.state.worker.port.postMessage({'action': 'setActiveChannel', 'room': this.state.channels[name]});
    },
    setLoading: function() {
      this.setState({
        ready: false
      }, function() {
        if( timer !== null ) {
          clearTimeout(timer);
        }
        timer = setTimeout(function() {
          this.setReady();
        }.bind(this), 100);
      }.bind(this));
    },
    setReady: function() {
      this.setState({
        ready: true
      });
    },
    renderChannels: function() {
      var channels = [];
      var directMessages = [];
      var otherChannels = [];
      var that = this;

      if( this.state.channels === null ) {
        return [];
      }
      for( var item in this.state.channels ) {
        var channel = this.state.channels[item];
        var type = channel.t;

        if( type === undefined ) {
          otherChannels.push(D.option({}, '!' + channel.name));
          continue;
        }

        var text = channel.name;
        var list = channels;

        if( type === 'd' ) {
          list = directMessages;
        }

        var classList = 'castle-chat-channel-link';

        if( this.state.unreadChannels &&  this.state.unreadChannels.indexOf(channel.name) >= 0 ) {
          text = '* ' + text;
        }

        list.push(D.option({
          className: classList,
          value: channel._id
        }, [
          text
        ]
        ));
      }
      return D.select({
        value: this.state.activeRoom,
        onChange: function(e) {
          e.preventDefault();
          this.setActiveChannel(e.target.value);
        }.bind(this),
        id: 'castle-active-select',
        ref: 'channel'
      }, [
        channels,
        directMessages
      ]);
    },
    renderMessages: function() {
      if( this.state.messages ) {
        var messages = [];

        var messageList = this.state.messages;
        var room = this.state.activeRoom;

        var previousUser = '';
        var previousTime = '';

        for( var message in messageList[room] ) {
          var mess = messageList[room][message];
          var headerContent = [];
          var header = '';

          if( mess.user !== previousUser || mess.time != previousTime) {
            headerContent.push(D.strong({ className: 'castle-chat-message-user'}, mess.user));
            headerContent.push(D.span({ className: 'castle-chat-message-date'}, mess.time));
          }

          if( headerContent.length !== 0 ) {
            header = D.div({
              className: 'castle-chat-message-conversation-header'
            }, [
              headerContent,
              D.br({})
            ]);
          }

          previousUser = mess.user;
          previousTime = mess.time;

          var classList = 'castle-chat-message-text';

          if( mess.type === 'uj' ) {
            classList += ' castle-chat-joined';
            mess.text = 'Has joined the channel.';
          }

          messages.push(
            D.li({}, [
              header,
              D.span({
                className: classList
              }, mess.text)
            ])
          );
        }

        return messages;
      }
      return [];
    },
    render: function() {
      if( !this.state.valid ) {
        console.log(this.state.error);
        return D.div({}, "Unable to connect to chat server.");
      }

      var channels = this.renderChannels();
      var messages = [];

      // if !ready, this means we're probably still actively receiving messages
      // otherwise, we'd re-render every time a message came in during the initial load
      if( this.state.ready ) {
        messages = this.renderMessages();
      }

      var disabled = '';
      if( this.state.activeRoom === null ) {
        disabled = 'disabled';
      }

      var content = [
        D.div({
          id: 'castle-chat-messenger-box',
          className: 'row'
        }, [
          D.div({}, [
            D.div({
              id: 'castle-chat-channel-box',
            }, channels)
          ]),
          D.ul({
            id: 'castle-chat-message-box',
          }, messages)
        ]),
        D.textarea({
          ref: 'messageBox',
          onKeyPress: function(e) {
            var code = (e.keyCode ? e.keyCode : e.which);
            if( code === 13 ) {
              this.sendMessage();
            }
          }.bind(this)
        }),
        D.button({
          onClick: function() {
            this.sendMessage();
          }.bind(this),
          disabled: disabled
        }, 'Send')
      ];
      return D.div({id: 'rocketchat'}, content);
    }
  });

  var ChatPattern = Base.extend({
    name: 'chat',
    trigger: '.pat-chat',
    parser: 'mockup',
    defaults: {},
    init: function () {
      var that = this;

      //return chatComponent;
      var data = JSON.parse(document.getElementById("castle-chat-data").innerHTML);
      R.render(R.createElement(chatComponent, data), document.getElementById("castle-chat"));
    }
  });

  return ChatPattern;

});
