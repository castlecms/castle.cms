/* global localStorage */

define([
  'jquery',
  'mockup-patterns-base',
  'pat-registry',
  'mockup-utils',
  'castle-url/components/utils',
  'castle-url/libs/react/react.min',
  'mockup-patterns-modal',
  'castle-url/patterns/toolbar/menu-item',
  'castle-url/patterns/toolbar/modal-item',
  'castle-url/components/add-content-modal',
  'castle-url/components/preview-content-modal',
  'castle-url/components/quality-check-modal',
  'castle-url/components/analytics-modal',
  'castle-url/components/workflow-modal',
  'castle-url/components/slot-manager-modal',
  'castle-url/components/design-modal',
  'moment'
], function ($, Base, Registry, utils, cutils, R, ModalPattern, MenuItemBase,
             ModalMenuItemBase, AddContentModal, PreviewContentModal, QualityCheckModal,
             AnalyticsModal, WorkflowModal, SlotManagerModal, DesignModal,
             moment) {
  'use strict';

  var D = R.DOM;
  var included_items = [];

  var MenuItem = R.createClass(MenuItemBase);

  var ViewPageMenuItem = cutils.Class([MenuItemBase], {
    isActive: function(){
      return ($('body').attr('data-base-url') === window.location.href ||
              MenuItemBase.isActive.apply(this));
    }
  });


  var ModalMenuItemFactory = function(Component, id){
    return cutils.Class([ModalMenuItemBase], {
      getDefaultProps: function(){
        return cutils.extend(ModalMenuItemBase.getDefaultProps.apply(this), {
          ModalComponent: Component,
          id: id
        });
      }
    });
  };

  var PatternModalItemBase = cutils.extend(MenuItemBase, {
    componentDidMount: function(){
      var modal = new ModalPattern($(this.refs.a.getDOMNode()), this.props);
      modal.$el.off('after-render');
      modal.on('after-render', function(){
        $('input[name*="cancel"]', modal.$modal).off('click').on('click', function() {
          // Close overlay
          modal.hide();
        });
      });
    }
  });
  var PatternModalItemFactory = function(opts){
    return cutils.Class([PatternModalItemBase], {
      getDefaultProps: function(){
        return opts;
      }
    });
  };

  var AddMenuItem = cutils.Class([ModalMenuItemBase], {
    getSettings: function(){
      return cutils.extend(this.props.parent.props.add, {
        parent: this.props.parent
      });
    },
    getDefaultProps: function(){
      return cutils.extend(ModalMenuItemBase.getDefaultProps.apply(this), {
        ModalComponent: AddContentModal,
        id: 'add-modal-react-container'
      });
    }
  });
  var WorkflowMenuItem = cutils.Class([ModalMenuItemBase], {
    getSettings: function(){
      return {
        parent: this.props.parent,
        workflow: this.props.parent.props.workflow
      };
    },
    getWorkflow: function(){
      return this.props.parent.props.workflow;
    },
    getClassName: function(){
      var className = MenuItemBase.getClassName.apply(this);
      var workflow = this.getWorkflow();
      if(workflow){
        className += ' state-' + workflow.state.id;
      }
      return className;
    },
    getLabel: function(){
      var workflow = this.getWorkflow();
      if(workflow){
        return this.props.item.title + ': ' + workflow.state.title;
      }else{
        return this.props.item.title;
      }
    },
    getDefaultProps: function(){
      return cutils.extend(ModalMenuItemBase.getDefaultProps.apply(this), {
        ModalComponent: WorkflowModal,
        id: 'workflow-modal-react-container'
      });
    }
  });

  var SlotsMenuItem = cutils.Class([ModalMenuItemBase], {
    getSettings: function(){
      return {
        parent: this.props.parent
      };
    },
    getDefaultProps: function(){
      return cutils.extend(ModalMenuItemBase.getDefaultProps.apply(this), {
        ModalComponent: SlotManagerModal,
        id: 'slot-manager-modal-react-container'
      });
    }
  });

  var DesignMenuItem = cutils.Class([ModalMenuItemBase], {
    getSettings: function(){
      return {
        parent: this.props.parent
      };
    },
    getDefaultProps: function(){
      return cutils.extend(ModalMenuItemBase.getDefaultProps.apply(this), {
        ModalComponent: DesignModal,
        id: 'design-modal-react-container'
      });
    }
  });


  var MenuItemRenderer = {
    getDefaultProps: function(){
      return {
        showIcon: true,
        modal: false,
        itemMapping: {
        }
      };
    },
    addAdditionalMenuItems: function(items) {
      // Include menu items from external add-ons and
      // incorporate them into the toolbar
      var itemMapping = this.state.itemMapping;
      var menu_items = Object.keys(items);
      menu_items.forEach(function(key) {
        itemMapping[key] = items[key];
      });

      this.setState({
        'itemMapping': itemMapping
      });

    },
    renderMenuItem: function(item){
      if(item === 'spacer'){
        return D.li({ className: 'spacer'});
      }

      var Component = MenuItem;
      if(this.state.itemMapping !== undefined && this.state.itemMapping[item.id]){
        Component = this.state.itemMapping[item.id];
      }else if(item.modal){
        Component = PatternModalItemFactory(item.modalAttributes);
      }
      return R.createElement(Component, {
        parent: this,
        item: item,
        showIcon: this.props.showIcon
      });
    }
  };


  var Dropdown = cutils.Class([MenuItemRenderer], {
    itemMapping: {
      impersonate: PatternModalItemFactory({
        actionOptions: {disableAjaxFormSubmit: true, redirectOnResponse:true}}),
    },
    getInitialState: function(){
      return {
        open: false
      };
    },
    getDefaultProps: function(){
      return {
        name: '',
        items: [],
        title: '',
        icon: '',
        onClick: function(){},
        showIcon: false
      };
    },
    btnClicked: function(e){
      e.preventDefault();
      this.props.onClick(this);
      this.setState({
        open: !this.state.open
      });
    },
    render: function(){
      var that = this;
      var className = 'castle-btn-dropdown castle-btn-dropdown-' + this.props.name;
      var content = [D.button({ className: 'icon-' + this.props.icon + ' plone-btn plone-btn-default',
                                onClick: this.btnClicked}, [D.span({}, this.props.title)] )];
      if(this.state.open){
        className += 'opened';
        content.push(D.ul({}, that.props.items.map(function(item){
          return that.renderMenuItem(item);
        })));
      }
      return D.div({ className: className}, content);
    }
  });

  var ChatDropdown = cutils.Class([Dropdown], {
    getInitialState: function() {

      if( this.props.chat_info === null ) {
        return {};
      }

      this.checkMissedMessages();

      return {
        token: this.props.chat_info.token,
        open: false,
        missed: false
      };
    },
    checkMissedMessages: function() {

      var frontpage = this.props.chat_info.frontpage;
      if( frontpage === undefined || frontpage === null ) {
        return;
      }

      if( frontpage.lastIndexOf('/') !== frontpage.length - 1 ) {
        frontpage += '/';
      }

      var url = frontpage + 'api/messageWaiting';

      var data = {
        token: this.props.chat_info.token,
        user: {
          email: this.props.chat_info.email,
          name: this.props.username
        }
      };

      $.ajax({
        url: url,
        data: data,
        method: 'POST'
      }).done(function(res) {
        this.setState({
          missed: res
        });
      }.bind(this));
    },
    renderChannels: function() {

      var that = this;
      var missed = this.state.missed;
      var rooms = Object.keys(this.state.missed);

      var output = [];

      for( var room in rooms ) {
        room = rooms[room];
        var messageClass = '';

        output.push(D.li({
          className: 'castle-chat-missed-channel'
        }, [
          D.div({className: 'castle-chat-channel-header' }, [
            room,
            D.span({className: 'castle-chat-missed'}, missed[room].length.toString()),
          ]),
          D.ul({}, that.renderMessages(missed[room]))
        ]));
      }

      return output;
    },
    renderMessages: function(messages) {
      var output = [];
      var count = 0;
      var previousAuthor = '';

      for( var message in messages ) {
        count += 1;

        //Put a cap on the # of missed messages
        if( count == 10 ) {
          output.push(
          D.div({className: 'castle-chat-divider-link'},
            D.a({
              className: 'castle-chat-missed-message',
              href: this.props.chat_info.frontpage + 'plone/' + this.state.token,
              target: '_blank'
            }, 'View more'))
          );
          return output;
        }

        message = messages[message];
        var author = [];

        //Don't keep repeating the username if they're
        //sending multiple messages.
        if( previousAuthor !== message.u.username ) {
          author = D.div({className: 'castle-chat-username'}, message.u.username + ': ');
        }

        previousAuthor = message.u.username;

        output.push(
          D.li(
            {
              className: 'castle-chat-missed-message'
            }, [
              author,
              message.msg])
        );
      }

      return output;
    },
    render: function() {

      if( this.props.chat_info === null ) {
        return null;
      }

      if( window.location.href.indexOf('/chat') >= 0 ) {
        return null;
      }

      if( this.props.chat_info.frontpage === null || this.props.chat_info.chat_url === null ) {
        return null;
      }

      var classList = 'plone-btn plone-btn-default chat-link';
      var rooms = '';

      if( this.state.missed ) {
        classList += ' chat-alert';
      }

      var content = [
        D.button({
          className: classList,
          onClick: this.btnClicked
        }, 'Chat')
      ];

      if( this.state.open ) {
        var dropdownContent = [];
        var message = 'No new messages';
        var broken = false;

        if( this.props.chat_info.email === "" ) {
          broken = true;
          message = 'A valid email must be associated with your profile before using chat';
        }

        if( this.state.missed ) {
          var roomNames = Object.keys(this.state.missed);
          var missed = this.state.missed;

          var roomMessages = this.renderChannels();

          dropdownContent.push(
            D.ul({className: 'castle-chat-preview'}, roomMessages)
          );
        }else{
          dropdownContent.push(D.div({className: 'castle-chat-empty'}, message));
        }
        var href = this.props.chat_info.frontpage + 'plone/' + this.state.token;
        href += '/' + this.props.username + '/' + this.props.chat_info.email;

        if( !broken ) {
          dropdownContent.push(
            D.div({className: 'castle-chat-goto-link'},
              D.a({
                href: href,
                disabled: broken,
                target: '_blank',
                className: 'castle-chat-bottom-link'
              }, 'Open chat')
            )
          );
        }

        content.push(D.div({className: 'castle-chat-dropdown'}, dropdownContent));
      }

      return D.div({
        className: 'castle-btn-dropdown',
        id: 'castle-chat-menu-item'
      }, content);
    }
  });

  var MessagesDropdown = cutils.Class([Dropdown], {
    // use local storage to track read messages
    // a read message is one that is shown
    infoIcon: D.svg({ id: "557c1826-141b-488e-8cbf-023297e947fc", 'data-name': "Layer 1",
                      xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 20 20"}, [
      D.defs({}, D.style({}, '.\\37 41286a0-08da-4764-b1d8-fc4a2fdaf01d{fill:#5bc0de;}')),
      D.path({ className: "741286a0-08da-4764-b1d8-fc4a2fdaf01d",
               d: "M10,.1A9.9,9.9,0,1,0,19.9,10,9.9,9.9,0,0,0,10,.1ZM9.8,15.5h.5a6,6,0,0,0,1.1-1.3l.3.2q-1.5,2.6-3.2,2.6a1.4,1.4,0,0,1-1-.4,1.2,1.2,0,0,1-.4-.9,3.4,3.4,0,0,1,.2-.9l1.4-4.7a4,4,0,0,0,.2-1,.5.5,0,0,0-.2-.4l-.5-.2H7.9V8.1l3.3-.5h.6l-2,7a3.9,3.9,0,0,0-.2.8Zm2.5-10a1.4,1.4,0,0,1-2.5-1,1.4,1.4,0,0,1,.4-1,1.4,1.4,0,0,1,2,0,1.4,1.4,0,0,1,.4,1A1.4,1.4,0,0,1,12.4,5.5Z"
             })
    ]),
    warningIcon: D.svg({ id: "43116b3f-bcf4-4eff-a6a9-4ce4def2b718", 'data-name': "Layer 1",
                      xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 20 20"}, [
      D.defs({}, D.style({}, '.\\32 928bb63-e350-4856-b63e-f748b9d2849c{fill:#efac4c;}')),
      D.path({ className: "2928bb63-e350-4856-b63e-f748b9d2849c",
               d: "M10,1.1.1,18.2H19.9ZM9,5.7a1.4,1.4,0,0,1,2,0,1.3,1.3,0,0,1,.4,1A12.2,12.2,0,0,1,10.9,9l-.4,1.8a14.8,14.8,0,0,0-.3,2.2H9.8a13.4,13.4,0,0,0-.4-2.2L9,9a11.3,11.3,0,0,1-.4-2.3A1.4,1.4,0,0,1,9,5.7Zm1.9,10.7a1.3,1.3,0,0,1-2.3-.9,1.3,1.3,0,0,1,.4-.9,1.3,1.3,0,0,1,1.9,0,1.3,1.3,0,0,1,0,1.9Z"
             })
    ]),
    errorIcon: D.svg({ id: "28e26966-46bc-480e-ae10-740701234303", 'data-name': "Layer 1",
                      xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 20 20"}, [
      D.defs({}, D.style({}, '.\\35 80fe009-4c8c-460f-b362-42cfa88ea0f5{fill:#d85450;}')),
      D.path({ className: "580fe009-4c8c-460f-b362-42cfa88ea0f5",
               d: "M14.1.1H5.9L.1,5.9v8.2l5.8,5.8h8.2l5.8-5.8V5.9ZM11.2,16.6a1.6,1.6,0,0,1-2.8-1.1,1.6,1.6,0,0,1,.5-1.2,1.6,1.6,0,0,1,2.3,0,1.6,1.6,0,0,1,0,2.3Zm0-9.2-.5,2.2a18.2,18.2,0,0,0-.4,2.8H9.8a16.5,16.5,0,0,0-.5-2.8L8.8,7.4a13.9,13.9,0,0,1-.5-2.8,1.7,1.7,0,0,1,.5-1.2A1.6,1.6,0,0,1,10,2.9a1.6,1.6,0,0,1,1.7,1.7A15,15,0,0,1,11.2,7.4Z"
             })
    ]),

    maxMessages: 50,

    getInitialState: function(){
      return {
        open: false,
        messages: this.props.items,
        unread: [],
        showUnread: false
      };
    },

    getDataKey: function(){
      return $('body').attr('data-portal-url') + this.props.user_id + 'readmessages';
    },

    getStoredData: function(){
      var key = this.getDataKey();
      var data = localStorage.getItem(key);
      if(!data){
        data = {
          messages: [],
          timestamps: []
        };
      }else{
        data = JSON.parse(data);
      }
      return data;
    },

    componentDidMount: function(){
      // load local storage data
      // set info on unread messages
      // show fade open unread if possible
      var that = this;
      var data = this.getStoredData();
      var unread = [];
      this.props.items.forEach(function(item){
        var timestamp = item.timestamp + '';
        if(data.timestamps.indexOf(timestamp) === -1){
          data.timestamps.push(timestamp);
          data.messages.unshift(item);
          unread.push(timestamp);
        }
      });

      // finally, trim messages
      var removed = data.messages.splice(this.maxMessages, data.messages.length + 1);
      removed.forEach(function(item){
        var timestamp = item.timestamp + '';
        var idx = data.timestamps.indexOf(timestamp);
        if(idx === -1){
          data.timestamps.splice(idx, 1);
        }
      });

      if(unread.length > 0){
        this.setState({
          showUnread: true,
          unread: unread,
          open: true,
          messages: data.messages
        }, function(){
          // fade out and close after some time
          setTimeout(function(){
            if(!that.refs.menuItems){
              return;
            }
            $(that.refs.menuItems.getDOMNode()).fadeOut(function(){
              that.setState({
                open: false,
                showUnread: false
              });
            });
          }, 3000);
        });
      }else{
        this.setState({
          messages: data.messages
        });
      }
      localStorage.setItem(this.getDataKey(), JSON.stringify(data));
    },

    getIcon: function(item){
      if(item.type === 'info'){
        return this.infoIcon;
      }
      if(item.type === 'warning'){
        return this.warningIcon;
      }
      if(item.type === 'error'){
        return this.errorIcon;
      }
    },

    btnClicked: function(e){
      e.preventDefault();
      this.props.onClick(this);
      this.setState({
        open: !this.state.open,
        showUnread: false
      });
    },

    renderMenuItem: function(item){
      var loc = '';
      if(item.context){
        loc = D.div({ className: 'location' }, [
          D.span({}, 'Location: '),
          D.span({ className: 'link' },
            D.a({ href: $('body').attr('data-portal-url') + item.context }, item.context || '/'))
        ]);
      }
      return D.li({ className: 'castle-status-message-item ' + item.type}, [
        D.div({ className: 'row'}, [
          D.div({ className: 'col-md-1 svg-container'}, this.getIcon(item)),
          D.div({ className: 'col-md-11'}, [
            D.div({ className: 'date' }, moment(new Date(item.timestamp * 1000)).fromNow()),
            D.div({ className: 'text' }, item.text),
            loc
          ])
        ])
      ]);
    },

    render: function(){
      var that = this;
      var className = 'castle-btn-dropdown castle-btn-dropdown-' + this.props.name;
      var unread = '';
      if(that.state.unread.length > 0){
        unread = D.span({ className: 'castle-toolbar-unread-message-count'}, that.state.unread.length);
      }
      var content = [D.button({ className: ' plone-btn plone-btn-default',
                                onClick: this.btnClicked}, [
          unread,
          'Notifications'
        ])];
      if(this.state.open){
        className += 'opened';
        var messages = [];
        that.state.messages.forEach(function(item){
          if(!that.state.showUnread || that.state.unread.indexOf(item.timestamp + '') !== -1){
            messages.push(item);
          }
        });
        content.push(D.ul({ ref: 'menuItems'}, messages.map(function(item){
          return that.renderMenuItem(item);
        })));
      }
      return D.div({ className: className}, content);
    }
  });

  var TopToolbar = R.createClass({
    renderBreadcrumbs: function(){
      var that = this;
      return D.ol({ className: 'castle-toolbar-breadcrumbs'}, [
        D.li({ className: 'castle-toolbar-crumb castle-toolbar-crumb-home'}, D.a({ href: $('body').attr('data-portal-url')}, 'Home'))
      ].concat(that.props.breadcrumbs.map(function(crumb){
        var className = 'castle-toolbar-crumb castle-toolbar-crumb-' + crumb.Title.toLowerCase().split(' ').join('-');
        if(crumb.state){
          className += ' crumb-state-' + crumb.state;
        }
        return D.li({ className: className}, D.a({ href: crumb.absolute_url }, crumb.Title));
      })));
    },
    btnClicked: function(btn){
      // close if open
      if(this.refs.cog && 'cog' !== btn.props.icon && this.refs.cog.state.open){
        this.refs.cog.setState({
          open: false
        });
      }
      if(this.refs.chat && 'chat' !== btn.props.name && this.refs.chat.state.open){
        this.refs.chat.setState({
          open: false
        });
      }
      if(this.refs.user && 'user' !== btn.props.name && this.refs.user.state.open){
        this.refs.user.setState({
          open: false
        });
      }
      if(this.refs.messages && 'messages' !== btn.props.name && this.refs.messages.state.open){
        this.refs.messages.setState({
          open: false
        });
      }
    },
    render: function(){
      var imgSrc = [D.img({ src: $('body').attr('data-portal-url') + '/++plone++castle/images/castle-logo.png', alt:'CastleCMS'})];
      return D.div({className: 'castle-toolbar-container-top'}, [
         D.a({ href:$('body').attr('data-portal-url'), className: 'castle-toolbar-logo'}, imgSrc),
        this.renderBreadcrumbs(),
        D.div({ className: 'castle-toolbar-buttons', onClick: function(e){
            e.stopPropagation();
          }}, [
          R.createElement(ChatDropdown, {
            chat_info: this.props.chat_info,
            username: this.props.user.name,
            onClick: this.btnClicked,
            ref: 'chat',
            name: 'chat'
          }),
          R.createElement(MessagesDropdown, { items: this.props.messages,
                                              user_id: this.props.user_id,
                                              ref: 'messages', onClick: this.btnClicked, name: 'messages'}),
          R.createElement(Dropdown, {icon: 'cog', items: this.props.management_menu,
                                     ref: 'cog', onClick: this.btnClicked, name: 'cog', title: 'Site Settings'}),
          R.createElement(Dropdown, {icon: 'user', title: this.props.user.name, ref: 'user',
                                     items: this.props.user_menu, onClick: this.btnClicked,
                                     name: 'user'})
        ])
      ]);
    }
  });


  var SideToolbar = cutils.Class([MenuItemRenderer], {
    getInitialState: function() {
      return {
        'hideButtons': true,
        'itemMapping': {
          'view-page': ViewPageMenuItem,
          add: AddMenuItem,
          quality: ModalMenuItemFactory(QualityCheckModal, 'quality-modal-react-container'),
          preview: ModalMenuItemFactory(PreviewContentModal, 'preview-modal-react-container'),
          analytics: ModalMenuItemFactory(AnalyticsModal, 'analytics-modal-react-container'),
          slots: SlotsMenuItem,
          design: DesignMenuItem,
          state: WorkflowMenuItem,
          rename: PatternModalItemFactory({
            actionOptions: {disableAjaxFormSubmit: true, redirectOnResponse:true}}),
          delete: PatternModalItemFactory({
            loadLinksWithinModal: false,
            actionOptions: {disableAjaxFormSubmit: true, redirectOnResponse:true, displayInModal: false}}),
          trash: PatternModalItemFactory({
            actionOptions: {disableAjaxFormSubmit: true, redirectOnResponse:true}}),
          invalidate: PatternModalItemFactory({}),
          aliases: PatternModalItemFactory({}),
          syndication: PatternModalItemFactory({
            actionOptions: {disableAjaxFormSubmit: true, redirectOnResponse:true}})
        }
      };
    },
    getMore: function(items) {
      var visible = 'none';

      if( !this.state.hideButtons ) {
        visible = 'inherit';
      }

      if( items.length === 0 ) {
        // below rendered a empty span tag when it wasn't in the more ul
        return null;
      }

      return D.li({
        ref: 'moreMenu',
        className: 'castle-toolbar-item'
      }, [
        D.a({
          href: '#',
          onClick: function(e) {
            e.preventDefault();
            this.setState({
              hideButtons: !this.state.hideButtons
            });
          }.bind(this)
        }, [ D.span({className: 'icon-add'}), D.span({}, 'More')]),
        D.ul({
          className: 'castle-toolbar-btn-container',
          style: {
            'display': visible
          }
        }, items)
      ]);
    },
    render: function(){
      var that = this;
      var hidden = [];
      var count = that.props.main_menu.length;

      var numHidden = that.props.hidden || 0;

      var buttons = that.props.main_menu.map(function(item){
        count -= 1;
        if( count < numHidden ) {

          hidden.push( that.renderMenuItem(item) );
          return;
        }
        return that.renderMenuItem(item);
      });
      buttons.push(this.getMore(hidden));
      return D.div({ className: 'castle-toolbar-container-side'}, D.ul({}, buttons));
    }
  });

  var Toolbar = R.createClass({
    getInitialState: function() {
      return {
        'hiddenButtons': 0
      };
    },
    render: function(){
      return D.div({ className: 'castle-toolbar-container'}, [
        R.createElement(TopToolbar, cutils.extend(this.props, { ref: 'top'})),
        R.createElement(SideToolbar, cutils.extend(this.props,
          {
            ref: 'side',
            hidden: this.state.hiddenButtons
          }
        ))
      ]);
    },
    calculateHidden: function() {
      var sideMenu = this.refs.side;
      var buttons = {};

      try {
        buttons = $(sideMenu.getDOMNode()).find('li');
      } catch(e){
        return;
      }

      var toolbarHeight = 0;

      // Need to account for the top menu bar
      var windowHeight = $(window).height() - $(this.refs.top.getDOMNode()).height();

      // If there are already hidden buttons, their height appears as 0
      // so we need to account for their real height.
      var buttonHeight = $(buttons[0]).height() - 2;

      var hidden = 0;

      $(buttons).each(function() {
          var addheight = $(this).height();

          if( addheight === 0 && !$(this).hasClass('spacer') ) {
            addheight = buttonHeight;
          }

          toolbarHeight += addheight;

          if( toolbarHeight > windowHeight ) {
            hidden += 1;

            if( addheight > 0 && (toolbarHeight - addheight) < windowHeight ) {
              // This catches the case where the bottom edge is
              // part way through a button. We don't want the More
              // button to be partially cut off
              hidden += 1;
            }
          }
      });
      this.setState({
        'hiddenButtons': hidden
      });
    },
    loadAddonButtons: function () {
      // Include additional buttons from JS files registered by
      // add-ons
      //
      // currently this only works for the side toolbar.
      // The top toolbar is a lot more difficult to make extensible
      var buttons = this.props.addon_buttons;
      var paths = [];

      if(buttons.side_toolbar !== undefined) {
        paths = paths.concat(buttons.side_toolbar);
      }

      // if(buttons.top_toolbar !== undefined) {
      //   paths = paths.concat(buttons.top_toolbar);
      // }

      require(paths, function() {
        var buttons = {
          'top': {},
          'side': {}
        };

        var button_interface = ['name', 'menu', 'renderer'];

        // We have no idea how many add-ons we're getting,
        // so we can't define them ahead of time. So, for loop:
        for(var i = 0; i<arguments.length; i++) {
          var item = arguments[i];

          // check that the argument object meets our interface
          var props = Object.keys(item);
          if( button_interface.every(function(key) { return props.indexOf(key) >= 0; }) ) {
            var menu = this.refs[item.menu];
            var itemMapping = buttons[item.menu];
            itemMapping[item.name] = item.renderer;
          }else{
            continue;
          }
        }

        // this.refs.top.addAdditionalMenuItems(buttons.top);
        this.refs.side.addAdditionalMenuItems(buttons.side);

      }.bind(this)).bind(this);
    },
    componentDidMount: function() {
      this.calculateHidden();
      this.loadAddonButtons();
      window.addEventListener('resize', this.calculateHidden);
    },
    componentWillUnmount: function() {
      window.removeEventListener('resize', this.calculateHidden);
    }
  });

  var ToolbarPattern = Base.extend({
    name: 'castletoolbar',
    trigger: '.pat-castletoolbar',
    parser: 'mockup',
    defaults: {},
    init: function () {
      var that = this;

      var component = R.render(R.createElement(Toolbar, that.options), that.$el[0], function(){
        if(document.body.className.indexOf('toolbar-initialized') === -1){
          document.body.className += ' toolbar-initialized';
        }
        $('body').trigger('toolbar-initialized', that, component);
      });

      $(window).on('click', function(){
        component.refs.top.refs.cog.setState({
          open: false
        });
        component.refs.top.refs.user.setState({
          open: false
        });
        component.refs.top.refs.messages.setState({
          open: false,
          showUnread: false
        });
        component.refs.top.refs.chat.setState({
          open: false
        });
      });

      /* folder contents changes the context.
         This is for usability so the menu changes along with
         the folder contents context */
      $('body').off('structure-url-changed').on('structure-url-changed', function (e, path) {
        /* reload toolbar and slots */
        $.ajax({
          url: $('body').attr('data-portal-url') + path + '/@@castle-toolbar',
          data: {
            'fc-reload': 'yes'
          },
          dataType: 'json'
        }).done(function(data){
          /* update body attributes */
          $('body').attr(
            'data-base-url', data['data-base-url']).attr(
            'data-view-url', data['data-view-url']);

          /* reload toolbar now */
          that.$el.empty();
          R.render(R.createElement(Toolbar, data), that.$el[0]);
        });
      });
    }

  });

  return ToolbarPattern;
});
