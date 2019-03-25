/* global localStorage */

define([
  'jquery',
  'mockup-patterns-base',
  'pat-registry',
  'mockup-utils',
  'castle-url/components/utils',
  'castle-url/libs/react/react.min',
  'mockup-patterns-modal',
], function ($, Base, Registry, utils, cutils, R, ModalPattern) {
  'use strict';

  var D = R.DOM;

  var MenuItemBase = {
    getDefaultProps: function(){
      return {
        showIcon: true
      };
    },
    getInitialState: function(){
      return {
        hovered: false,
        focussed: false
      }
    },
    onClick: undefined,
    getLabel: function(){
      return this.props.item.title;
    },
    getClassName: function(){
      return 'castle-toolbar-item castle-toolbar-' + this.props.item.id;
    },
    stripQS: function(s){
      return s.split('?')[0];
    },
    isActive: function(){
      return this.stripQS(window.location.href) === this.stripQS(this.props.item.url);
    },
    render: function(){
      var item = this.props.item;
      var className = this.getClassName();
      if(this.isActive()){
        className += ' active';
      }
      var icon = '';
      if(this.props.showIcon === undefined || this.props.showIcon){
        icon = D.span({ className: item.icon_class, 'aria-hidden': true });
      }
      return D.li(
        { className: className}, [
          D.span({ className: 'simpletooltip_container'}, [
            D.a({ href: item.url, onClick: this.onClick,
                  ref: 'a', className: 'js-simple-tooltip',
                  onFocus: function(){
                    this.setState({
                      focussed: true
                    });
                  }.bind(this),
                  onMouseEnter: function(){
                    this.setState({
                      hovered: true
                    });
                  }.bind(this),
                  onBlur: function(){
                    this.setState({
                      focussed: false
                    });
                  }.bind(this),
                  onMouseLeave: function(){
                    this.setState({
                      hovered: false
                    });
                  }.bind(this),
                  onKeyDown: function(){
                    if (event.keyCode == 27) { // esc
                      this.setState({
                        focussed: false
                      });
                    }
                  }.bind(this),
                  'aria-describedby': 'label_simpletooltip_' + this.props.item.id}, [
            icon,
            this.getLabel()
          ]),
          D.span({ className: 'js-simpletooltip simpletooltip',
                   id: 'label_simpletooltip_' + this.props.item.id,
                   'aria-hidden': !this.state.focussed && !this.state.hovered,
                   'role': 'tooltip'},
            this.props.item.description)
          ])
      ]);
    }
  };
  return MenuItemBase;
});
