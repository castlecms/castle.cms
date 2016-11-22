define([
  'castle-url/libs/react/react.min'
], function(R){
  'use strict';

  var D = R.DOM;

  return R.createClass({

    render: function(){
      return D.input({ type: 'text', onChange: this.props.onChange,
                       value: this.props.value,
                       className: 'querystring-criteria-value-StringWidget form-control' });
    }
  });

});
