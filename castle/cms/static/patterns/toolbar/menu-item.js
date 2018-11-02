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
        { className: className},
        D.a({ href: item.url, onClick: this.onClick, ref: 'a'}, [
          icon,
          this.getLabel()
        ]));
    }
  };
  return MenuItemBase;
});
