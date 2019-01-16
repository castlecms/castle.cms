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
         [D.span({ className: 'simpletooltip_container'}, [D.a({ href: item.url, onClick: this.onClick, ref: 'a', className: 'js-simple-tooltip', 'data-simpletooltip-text': this.props.item.description, 'aria-describedby': 'label_simpletooltip_' + this.props.item.id}, [
          icon,
          this.getLabel()
        ])], [D.span({ className: 'js-simpletooltip simpletooltip', id: 'label_simpletooltip_' + this.props.item.id, 'aria-hidden': true, 'role': 'tooltip'}, this.props.item.description)])]);
    }
  };
  
    // Wait a bit when the complete page is fully loaded
    // from https://github.com/nico3333fr/jquery-accessible-simple-tooltip-aria
    $(window).load(function() {
        //events ------------------
        $('body')
            .on('mouseenter focusin', '.js-simple-tooltip', function() {
                var $this = $(this);
                var aria_describedby = $this.attr('aria-describedby');
                var tooltip_to_show_id = aria_describedby;
                var $tooltip_to_show = $('#' + tooltip_to_show_id);
                $tooltip_to_show.attr('aria-hidden', 'false');
            })
            .on('mouseleave', '.js-simple-tooltip', function(event) {
                var $this = $(this);
                var aria_describedby = $this.attr('aria-describedby');
                var tooltip_to_show_id = aria_describedby;
                var $tooltip_to_show = $('#' + tooltip_to_show_id);
                var $is_target_hovered = $tooltip_to_show.is(':hover');

                //alert($target_hovered);
                //$target.addClass('redborder');
                if (!$is_target_hovered) {
                    $tooltip_to_show.attr('aria-hidden', 'true');
                }
            })
            .on('focusout', '.js-simple-tooltip', function(event) {
                var $this = $(this);
                var aria_describedby = $this.attr('aria-describedby');
                var tooltip_to_show_id = aria_describedby;
                var $tooltip_to_show = $('#' + tooltip_to_show_id);

                $tooltip_to_show.attr('aria-hidden', 'true');
            })
            .on('mouseleave', '.js-simpletooltip', function() {
                var $this = $(this);
                $this.attr('aria-hidden', 'true');
            })
            .on('keydown', '.js-simple-tooltip', function(event) {
                // close esc key

                var $this = $(this);
                var aria_describedby = $this.attr('aria-describedby');
                var tooltip_to_show_id = aria_describedby;
                var $tooltip_to_show = $('#' + tooltip_to_show_id);

                if (event.keyCode == 27) { // esc
                    $tooltip_to_show.attr('aria-hidden', 'true');
                }
            });
    });
  return MenuItemBase;
});
