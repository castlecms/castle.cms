define([
  'castle-url/libs/react/react.min',
  'castle-url/addsite/store',
  'castle-url/addsite/actions',
  'castle-url/addsite/validators'
], function(React, Store, Actions, validators){

  var D = React.DOM;

  var selectType = function(type) {
    var inputClass = null;
    switch (type) {
      case 'select':
        inputClass = SelectInput;
        break;
      case 'checkbox':
        inputClass = CheckboxInput;
        break;
      case 'fieldset':
        inputClass = FieldsetInput;
        break;
      default:
        inputClass = Input;
        break;

    }
    return inputClass;
  };

  var runValidation = function(that, value) {
    var errors = [];

    for(var test in that.props.validators){

      var name = that.props.validators[test];
      var error = validators[name](value);

      if( error !== '' ) {
        errors.push(error);
      }
    }

    if( errors.length > 0 ) {
      that.props.validate(false);

      //This isn't the most valid way to do this, but
      //we need a way to synchronously communicate back
      //the the setup form whether or not this has failed
      that.state.valid = false;
      that.setState({
        touched: true,
        errorText: errors[0]
      });
    }
    else{
      that.props.validate(true);
      that.setState({
        valid: true,
        touched: true,
        errorText: null
      });
    }
  };

  var validate = function(e) {

    this.state.touched = true;

    if(this.state.timer){
      clearTimeout(this.state.timer);
    }

    var errors = [];
    var that = this;
    var value = e.target.value;

    if( e.target.type === "checkbox" ) {
      if( e.target.checked ) {
        value = true;
      }
      else{
        value = false;
      }
    }

    if( e.target.type === "file" ) {
      var r = new FileReader();
      var file = e.target.files[0];
      var filename = e.target.value;

      if( !filename ) {
          //Clear everything out
          Actions.update(this.props.name, null);
          this.setState({
            image: null,
            defaultValue: null
          });
          return;
      }

      runValidation(this, filename);

      //Just get the filename, not the fakepath
      filename = filename.substr( filename.lastIndexOf('\\') + 1 );

      r.onloadend = function(name, img) {
        var output = 'filenameb64:';
        output += btoa(name) + ';datab64:';

        //We still want to render the image here, but
        //we need to parse it correctly for Plone to recognize it
        var file = img.target.result;
        var plone_file = file.substr(file.indexOf(',')+1);

        output += plone_file;

        Actions.update(this.props.name, {
          filename: name,
          filedata: file,
          output: output
        });

        this.setState({
          image: file
        });

      }.bind(that, filename);

      r.readAsDataURL(e.target.files[0]);

      return;
    }

    this.state.timer = setTimeout(function() {
      runValidation(that, value);
    }, 1000);

    Actions.update(that.props.name, value);
  };

  var getOverrides = function(props) {
    var output = {};
    for( var prop in props ) {
      var item = props[prop];

      //We want to preserve pointers to functions,
      //but not normal values.
      if( typeof(item) === "function" ) {
        output[prop] = item;
      }
      else if( item === null ) {
        //if it's null, we don't need this setting here
        continue;
      }
      else {
        output[prop] = item;
      }
    }

    return output;
  };
  var Input = React.createClass({
    statics: {
      buildInputOptions: function(props) {
        var options = {
          key: props.name,
          id: props.id,
          name: props.name,
          required: props.required || false,
          type: props.type,
          parent: props.parent || null,
          validators: props.validators || [],
          defaultValue: props.defaultValue,
          onChange: props.update || validate.bind(this),
        };

        if( options.type == "checkbox" && props.checked ) {
          options.defaultChecked = true;
        }

        return options;
      }
    },
    getInitialState: function() {
      var props = this.props;
      return {
        name: props.name,
        key: props.name,
        errors: props.errors || false,
        formHelp: props.formHelp || null,
        type: props.type || null,
        labelText: props.labelText || null,
        defaultValue: props.defaultValue || null,
        image: props.image || null,
        touched: false,
        timer: 0
      };
    },
    componentWillMount: function() {
      //Allows us to do pseudo-overloading
      this.buildInputOptions = this.props.buildInputOptions || Input.buildInputOptions;
      this.buildInput = this.props.buildInput || this._buildInput;
      this.setDefault = this.props.setDefault || this._setDefault;
      this.render = this.props.render || this._render;

      if( this.props.type == "fieldset" ) {
        this.props.initialize(this.props.name, {});
      }else if( this.props.initialize ){
        this.props.initialize(this.props.name, this.props.defaultValue);
      }

      return this;
    },
    _buildInput: function(options) {
      return D.input(options);
    },
    _setDefault: function(value) {
      return "" + value;
    },
    _render: function() {
      var props = this.props;
      var state = this.state;
      var options = this.buildInputOptions(this.props);

      var order = props.inputOrder || ['label', 'help', 'errors', 'input'];

      var elements = [];

      //This allows us to specify the order of rendering,
      //Or to omit elements all together
      for( var element in order ) {
        var item = '';
        switch(order[element]) {
          case 'label':
            item = D.label({
              key: "label"
            }, state.labelText);
            break;

          case 'help':
            item = D.div({
              key: "formHelp",
              className: "formHelp"
            }, state.formHelp);
            break;

          case 'errors':
            item = D.span({
              key: "errors",
              className: "error",
            }, state.errorText);
            break;

          case 'input':
            options.className = "form-control";
            item = this.buildInput(options);
            break;

          case 'img':
            if( !state.image ){
              break;
            }
            item = D.img({
              key: 'image',
              src: state.image
            });
            break;
        }

        elements.push(item);
      }

      var className = "field";
      if( state.errorText !== undefined && state.errorText !== null ) {
        className += " has-error";
      }

      return D.div({
        className: className
      }, elements);
    },
    validateImmediately: function(value) {
      runValidation(this, value);
    },
    render: function() {
      //placeholder to make React happy
      return "";
    }
  });

  var SelectInput = React.createClass({
    buildInput: function(options) {
      var optionTags = [];

      if( this.props.dataSet ) {
        var data = this.props.dataSet;
        for( var item in data ) {
          optionTags.push(this.createOptGroup(item, data[item]));
        }
      }
      return D.select(options, optionTags);
    },
    createOption: function(label, value) {
      return D.option({
        value: value,
        key: this.props.name + "-" + label
      }, label);
    },
    createOptGroup: function(name, items) {
      var options = [];
      var self = this;
      for( var item in items ) {
        options.push(self.createOption(item, items[item]));
      }
      return D.optgroup({label: name, key: this.props.name + "-group-" + name}, options);
    },
    setDefault: function(value) {
      if( this.props.multiple ) {
        return [value];
      }else{
        return "" + value;
      }
    },
    render: function() {
      //We want to copy the props object, not reference it.
      var overrides = getOverrides(this.props);

      overrides.buildInput = this.buildInput;
      overrides.setDefault = this.setDefault;

      var input = React.createElement(Input, overrides);

      return input;
    }
  });

  var FieldsetInput = React.createClass({
    childUpdate: function(e) {
      var value = '';
      if( e.target.checked ) {
        value = e.target.checked;
      }else{
        value = e.target.value;
      }
      Actions.fieldsetUpdate(e.target.name, this.props.name, value);
    },
    buildInput: function() {
      var self = this;
      if( !this.props.dataSet || !this.props.dataValues ) {
        console.log("Missing data for " + this.props.name);
        return '';
      }
      var inputs = [];

      //TODO: This is currently only really setup to work with
      //Fieldsets made up of checkboxes. Needs to be more flexible.
      for( var item in this.props.dataSet ) {
        var input = this.props.dataSet[item];
        var inputProps = {
          name: input.name || item || null,
          id: input.name || item || null,
          parent: self.props.name,
          key: item,
          labelText: input.title,
          formHelp: input.description,
          type: input.type,
          checked: this.props.dataValues[item] || false,
          defaultValue: item,
          update: this.childUpdate
        };

        var inputClass = selectType(input.type);

        var name = this.props.name + '[' + inputProps.defaultValue + ']';

        var value = '';
        if( inputProps.type == "checkbox" ) {
          if( inputProps.checked ){
            value = true;
          }else{
            value = false;
          }
        }else{
          value = inputProps.defaultValue;
        }

        Actions.fieldsetUpdate(inputProps.name, this.props.name, value);

        inputs.push(React.createElement(inputClass, inputProps));
      }

      return D.fieldset({
        className: "fieldset"
      }, inputs);
    },
    componentWillMount: function() {
      this.props.initialize(this.props.name, {});
    },
    render: function() {
      var overrides = getOverrides(this.props);

      overrides.buildInput = this.buildInput;

      var input = React.createElement(Input, overrides);

      return input;
    }
  });

  var CheckboxInput = React.createClass({
    render: function() {
      var overrides = getOverrides(this.props);
      overrides.inputOrder = ['input', 'label', 'help', 'errors'];
      var input = React.createElement(Input, overrides);

      return input;
    }
  });

  var FileInput = React.createClass({
    render: function() {
      var overrides = getOverrides(this.props);

      if( overrides.isImage ) {
        overrides.inputOrder = ['label', 'help', 'errors', 'img', 'input'];
      }
      var input = React.createElement(Input, overrides);

      return input;
    },
  });

  return {
    input: Input,
    select: SelectInput,
    fieldset: FieldsetInput,
    checkbox: CheckboxInput,
    file: FileInput
  };
});
