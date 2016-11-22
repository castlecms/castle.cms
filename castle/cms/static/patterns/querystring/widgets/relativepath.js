define([
  'jquery',
  'castle-url/libs/react/react.min'
], function($, R){
  'use strict';

  var D = R.DOM;

  return R.createClass({
    render: function(){
      return D.div({ className: 'querystring-relative-path'}, [
        D.select({ onChange: this.props.onChange,
                   value: this.props.value,
                   className: "form-control" }, [
          D.option({ value: ''}, 'Select'),
          D.option({ value: '../::1'}, 'Parent'),
          D.option({ value: './::1'}, 'Current')
        ])
      ]);
    }
  });

});
