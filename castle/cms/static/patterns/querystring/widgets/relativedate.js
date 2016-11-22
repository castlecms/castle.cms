define([
  'jquery',
  'castle-url/libs/react/react.min'
], function($, R){
  'use strict';

  var D = R.DOM;

  return R.createClass({
    onKeyDown: function(e){
      if([8, 9, 13, 27].indexOf(e.charCode || e.keyCode) !== -1){
        // valid characters
        return;
      }
      var val = String.fromCharCode (e.charCode || e.keyCode);
      if(isNaN(val)){
        e.preventDefault();
      }
    },

    render: function(){
      return D.input({ type: 'number', value: this.props.value,
                       onChange: this.props.onChange, onKeyDown: this.onKeyDown,
                       className: 'querystring-criteria-value-RelativeDateWidget' });
    }
  });

});
