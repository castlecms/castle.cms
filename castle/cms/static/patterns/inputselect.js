
define([
  'jquery',
  'castle-url/libs/react/react.min',
  'pat-base',
  'mockup-patterns-select2',
  'mockup-utils',
  'mockup-patterns-tree',
  'translate',
  'castle-url/components/content-browser',
  'castle-url/components/add-content-modal',
  'castle-url/components/utils'
], function($, R, Base, Select2, utils) {
  'use strict';

  var D = R.DOM;

  var OptionalInputComponent = R.createClass({
    render: function() {
      D.div({}, [
        D.label({},'test'),
        D.input({})
      ]);
    }
  });

  var InputSelect = Base.extend({
    name: 'inputselect',
    trigger: '.pat-inputselect',
    parser: 'mockup',
    hidden_input: null,
    $input: null,

    setValue: function(e) {
      var self = this;

      self.$el.val(self.$input.val());
      debugger;
    },
    setupHiddenInput: function() {
      var self = this;

      var label = 'Other';
      if( self.options.label !== undefined ) {
        label = self.options.label + ' ' + label;
      }

      self.hidden_input = $('' +
      '<div id="inputselect-container">' +
        '<label id="inputselect-label" for="inputselect-other">'+label+'</label>' +
        '<input id="inputselect-input" type="text" />' +
      '</div>');

      self.$el.after(self.hidden_input);
      self.hidden_input.hide();

      self.$input = self.hidden_input.find('#inputselect-input');
      self.$input.on('input', self.setValue.bind(self));
    },
    setSelectedValue: function(items) {
      var self = this;

      var val = self.options.value;
      var isSelected = function(item, val) {
        if( item.value == val ) {
          item.selected = true;
        }
        return item;
      };

      return items.map(function(item) {
        return isSelected(item, val);
      });
    },
    init: function() {
      var self = this;
      var initialItems = JSON.parse(self.options.initialItems);
      initialItems = self.setSelectedValue(initialItems);
      var options = {
        data: initialItems
      };

      self.setupHiddenInput();
      self.$el.select2({
        data: initialItems,
        width: '20em'
      });

      self.$el.on('change.select2', function(e) {
        var self = this;
        if( e.type === 'change' ) {
          if( e.added.id === 'other' ) {
            self.hidden_input.show();
          }else{

          }
        }
      }.bind(self));
    }
  });

  return InputSelect;
});
