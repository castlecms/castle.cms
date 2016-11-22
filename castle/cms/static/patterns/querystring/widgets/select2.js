define([
  'jquery',
  'castle-url/libs/react/react.min'
], function($, R){
  'use strict';

  var D = R.DOM;

  return R.createClass({

    getInitialState: function(){
      return {
        renderedValue: this.props.value,
        renderedOptions: this.props.options
      };
    },

    getDefaultProps: function(){
      return {
        value: '',
        width: '10em',
        multiple: false
      };
    },

    componentDidMount: function(){
      this.load();
    },

    load: function(){
      var that = this;
      var $input = $(this.refs.select.getDOMNode());
      $input.select2();
      $input.on('change', function(){
        if(that.props.onChange){
          that.props.onChange.call(that, {
            target: {
              value: $input.select2('val')
            }
          });
        }
      });
      if(this.props.value){
        $input.select2('val', this.props.value);
      }else{
        $input.select2('val', '');
      }
      that.state.renderedValue = this.props.value;
      that.state.renderedOptions = this.props.options;
    },

    componentDidUpdate: function(){
      // need to select or clear value
      var that = this;

      var $input = $(this.refs.select.getDOMNode());

      // first change if options changed, we need complete reload...
      if(JSON.stringify(that.state.renderedOptions) !== JSON.stringify(this.props.options)){
        // data changed, reload
        $input.select2("destroy");
        this.load();
      } else if(that.state.renderedValue !== this.props.value){
        // only data changed, manually change select2 now...
        $input.select2('val', that.props.value);
        that.state.renderedValue = this.props.value;
      }
    },

    render: function(){
      var options = [];
      var groups = {};
      this.props.options.forEach(function(option){
        var optionEl = D.option({ value: option.value }, option.label);
        if(option.group){
          if(!groups[option.group]){
            groups[option.group] = [];
          }
          groups[option.group].push(optionEl);
        }else{
          options.push(optionEl);
        }
      });
      for(var groupName in groups){
        options.push(D.optgroup({ label: groupName}, groups[groupName]));
      }
      return D.select({ ref: 'select', value: this.props.value,
                        style: { width: this.props.width },
                        multiple: this.props.multiple }, options);
    }
  });

});
