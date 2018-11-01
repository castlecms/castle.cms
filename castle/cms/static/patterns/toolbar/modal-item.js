/* global localStorage */

define([
  'jquery',
  'mockup-patterns-base',
  'pat-registry',
  'mockup-utils',
  'castle-url/components/utils',
  'castle-url/libs/react/react.min',
  'mockup-patterns-modal',
  'castle-url/patterns/toolbar/menu-item'
], function ($, Base, Registry, utils, cutils, R, ModalPattern, MenuItemBase) {
  'use strict';

  var D = R.DOM;

  var ModalMenuItemBase = cutils.extend(MenuItemBase, {
    onClick: function(e){
      e.preventDefault();
      cutils.createModalComponent(this.props.ModalComponent, this.props.id, this.getSettings());
    },
    getSettings: function(){
      return {
        parent: this.props.parent
      };
    }
  });

  return ModalMenuItemBase;
});
