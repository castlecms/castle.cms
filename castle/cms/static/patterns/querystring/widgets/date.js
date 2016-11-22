define([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-patterns-pickadate'
], function($, R, PickADate){
  'use strict';

  var D = R.DOM;

  return R.createClass({
    componentDidMount: function(){
      var that = this;
      var $input = $(that.refs.input.getDOMNode());
      var pickadate = new PickADate($input, {
        time: false
      });
      pickadate.on('updated.pickadate.patterns', function() {
        that.props.onChange.call(that, {
          target: {
            value: $input.val()
          }
        });
      });
    },

    componentDidUpdate: function(){
      var $input = $(this.refs.input.getDOMNode()).parent().find('.pattern-pickadate-date');
      if(!this.props.value){
        $input.pickadate('clear');
      }else{
        $input.pickadate('select', this.props.value);
      }
    },

    render: function(){
      return D.input({ className: 'pat-pickadate', ref: 'input',
                       value: this.props.value});
    }
  });

});
