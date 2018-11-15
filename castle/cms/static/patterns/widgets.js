/*

  Miscellaneous edit widgets

*/
define([
  'jquery',
  'pat-base',
  'castle-url/libs/react/react.min',
], function($, Base, R) {
  "use strict";
  
  var D = R.DOM;

  var UploadFieldsWidgetComponent = R.createClass({
    getDefaultProps: function(){
      return {
        'changeEvent': function(value){}
      };
    },

    getInitialState: function(){
      return {
        value: []
      };
    },

    notifyChange: function(){
      this.setState({
        value: this.state.value
      });
      this.props.changeEvent(this.state.value);
    },

    valueChanged: function(idx, name, widget, evt){
      if(widget == 'checkbox'){
        this.state.value[idx][name] = evt.target.checked;
      }else{
        this.state.value[idx][name] = evt.target.value;
      }
      this.notifyChange();
    },

    renderFieldField: function(name, label, value, fieldIdx){
      // "field" is top level value taht is being described
      var id = 'upload-fields-' + name + '-' + fieldIdx;

      var input;
      if(name === 'widget'){
        input = D.select({
          id: id, value: value,
          onChange: this.valueChanged.bind(this, fieldIdx, name, 'select') }, [
              D.option({ value: 'text' }, 'Text'),
              D.option({ value: 'textarea' }, 'Textarea'),
              D.option({ value: 'tags' }, 'Tags'),
              D.option({ value: 'checkbox' }, 'Checkbox'),
          ]);
      }else if(name === 'required'){
        if(typeof(value) == "string"){
          value = value === 'true';
        }
        input = D.input({
          id: id, type: 'checkbox', checked: value,
          onChange: this.valueChanged.bind(this, fieldIdx, name, 'checkbox') });
      }else{
        input = D.input({
          id: id, value: value,
          onChange: this.valueChanged.bind(this, fieldIdx, name, 'text') });
      }
      return D.li ({
        className: 'field', id: id + '-container'
      }, [
        D.label({ htmlFor: id }, label),
        input,
      ]);
    },

    removeClicked: function(idx, evt){
      evt.preventDefault();
      this.state.value.splice(idx, 1);
      this.notifyChange();
    },

    renderField: function(field, idx){
      return D.div({className: 'file-upload-field-container'}, [
        D.h4({}, field['label']),
        D.ul({ className: 'file-upload-fields'}, [
          this.renderFieldField('name', 'Name', field['name'], idx),
          this.renderFieldField('label', 'Label', field['label'], idx),
          this.renderFieldField('widget', 'Widget', field['widget'], idx),
          this.renderFieldField('required', 'Required', field['required'], idx),
          this.renderFieldField('for-file-types', 'For types', field['for-file-types'], idx)
        ]),
        D.button({ className: 'btn btn-danger btn-xs remove-btn',
                   onClick: this.removeClicked.bind(this, idx) }, 'Remove')
      ]);
    },

    addClicked: function(evt){
      evt.preventDefault();
      this.state.value.push({
        'name': 'fieldname',
        'label': 'Field label',
        'widget': 'text',
        'for-file-types': '*',
        'required': false
      })
      this.notifyChange();
    },

    render: function(){
      var items = [];
      var self = this;
      this.state.value.forEach(function(field, fieldIdx){
        items.push(self.renderField(field, fieldIdx))
      });
      return D.div({className: 'file-upload-fields-container'}, [
        D.div({}, items),
        D.button({ className: 'btn btn-primary btn-xs add-btn',
                   onClick: this.addClicked }, 'Add')
      ]);
    }
  });

  var UploadFieldsWidget = Base.extend({
    name: 'fileuploadfieldswidget',
    trigger: '.pat-fileuploadfieldswidget',
    parser: 'mockup',
    defaults: {
      timeout: 0
    },

    init: function() {
      var self = this;
      self.$el.hide();
      var $div = $('<div/>');
      self.$el.after($div);
      self.component = R.render(R.createElement(
        UploadFieldsWidgetComponent, {
          changeEvent: function(value){
            clearTimeout(self.options.timeout);
            self.options.timeout = setTimeout(function(){
              self.$el[0].setAttribute('value', JSON.stringify(value));
            }, 100);
          }
        }), $div[0]);

      var value = JSON.parse(self.$el.val());
      self.component.setState({
          value: value
      });
    }
  });

  return UploadFieldsWidget;

});

  

