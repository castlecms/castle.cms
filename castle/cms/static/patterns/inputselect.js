
define([
  'jquery',
  'castle-url/libs/react/react',
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

  var TextInputSelectComponent = R.createClass({
    getInitialState: function() {
      var self = this;

      return {
        hidden: !self.props.valueIsOther,
        value: self.props.inputValue
      };
    },
    checkInput: function(event) {
      var self = this;

      if( event.val == 'other' ) {
        self.showInput();
      }else{
        self.hideInput();
      }
    },
    renderInput: function() {
      return D.div({id: 'input'});
    },
    render: function() {
      var self = this;

      if( self.state.hidden ) {
        return D.div({});
      }

      return D.div({
          className: 'textinputselect-container form-group',
          key: 'container'
        }, [
        D.label({
          className: 'textinputselect-label', key: 'label'}, self.props.label + ' Other'),
        D.input({
          className: 'textinputselect-input form-control',
          key: 'input',
          defaultValue: self.state.value,
          onKeyUp: self.updateValue})
      ]);
    },
    hideInput: function() {
      var self = this;

      self.setState({
        hidden: true
      });
    },
    showInput: function() {
      var self = this;

      self.setState({
        hidden: false
      });
    },
    updateValue: function(event) {
      var self = this;

      self.props.input.val(event.currentTarget.value);
    }
  });

  var TextInputSelect = Base.extend({
    name: 'inputselect',
    trigger: '.pat-inputselect',
    parser: 'mockup',
    hidden_input: null,
    $input: null,

    setSelectedValue: function(items) {
      var self = this;

      var val = self.options.value;
      var found = false;
      var other = -1;

      if( val == '' || val === undefined ) {
        // Leave the select2 box empty if there's no value.
        self.hideTextInput = true;
        return items;
      }

      for( var i = 0; i < items.length; i++) {
        if( items[i].id == val ) {
          // We've found the value in the vocabulary
          items[i].selected = true;
          found = true;
          self.hideTextInput = true;
        }

        if( items[i].id == 'other' ) {
          other = i;
        }
      }

      if( other < 0 ) {
        // The vocabulary didn't include an 'other' option
        items.push({'id': 'other', 'text': 'Other'});
        other = items.length - 1;
      }

      if( !found ) {
        items[other].selected = true;
        self.hideTextInput = false;

        // need to temporarily change the value to
        // 'other' so the select2 box will render the
        // option correctly
        self.$el.val('other');
      }

      return items;
    },
    init: function() {
      var self = this;

      self.hideTextInput = true;

      var initialItems = JSON.parse(self.options.initialItems);
      initialItems = self.setSelectedValue(initialItems);

      var select2items = {
        'results': initialItems
      };

      self.$el.select2({
        data: select2items,
        width: '30em'
      });

      // We may have set the value to 'other' in order
      // to get seleect2 to render properly, let's set it back
      self.$el.val(self.options.value);

      var options = {
        data: initialItems,
        input: self.$el,
        label: self.options.label,
        inputValue: self.options.value,
        valueIsOther: !self.hideTextInput
      };

      var el = document.createElement('div');
      self.$el.parent().append(el);

      self.component = R.render(R.createElement(TextInputSelectComponent, options), el);

      self.$el.on('change.select2', function(e) {
        var self = this;
        if( e.type === 'change' ) {
          self.component.checkInput(e);
        }
      }.bind(self));
    }
  });

  return TextInputSelect;
});
