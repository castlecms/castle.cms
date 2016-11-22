define([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-patterns-pickadate'
], function($, R, PickADate){
  'use strict';

  var D = R.DOM;

  return R.createClass({
    getInitialState: function(){
      return {
        value: ['', '']
      };
    },

    componentDidMount: function(){
      var that = this;
      var $input1 = $(this.refs.input1.getDOMNode());
      this.props.pickadate1 = new PickADate($input1, {
        time: false
      });
      var $input2 = $(this.refs.input2.getDOMNode());
      this.props.pickadate2 = new PickADate($input2, {
        time: false
      });
      this.props.pickadate1.on('updated.pickadate.patterns', function() {
        if(!that.props.value){
          that.props.value = ['', ''];
        }
        that.props.value[0] = $input1.val();
        that.pushChange();
      });
      this.props.pickadate2.on('updated.pickadate.patterns', function() {
        if(!that.props.value){
          that.props.value = ['', ''];
        }
        that.props.value[1] = $input2.val();
        that.pushChange();
      });
    },

    componentDidUpdate: function(){
      var that = this;
      var $input1 = $(this.refs.input1.getDOMNode()).parent().find('.pattern-pickadate-date');
      var $input2 = $(this.refs.input2.getDOMNode()).parent().find('.pattern-pickadate-date');

      if(!that.props.value){
        that.props.value = ['', ''];
      }

      if(!this.props.value[0]){
        $input1.pickadate('clear');
      }else{
        $input1.pickadate('select', this.props.value[0]);
      }
      if(!this.props.value[1]){
        $input2.pickadate('clear');
      }else{
        $input2.pickadate('select', this.props.value[1]);
      }
    },

    pushChange: function(){
      this.props.onChange.call(this, {
        target: {
          value: this.props.value,
          force: true
        }
      }, true);
    },

    render: function(){
      var value = this.props.value;
      if(!value || !value[0] || !value[1]){
        value = ['', ''];
      }
      return D.div({ className: 'querystring-date-range' }, [
        D.span({ className: 'querystring-date-wrapper'},
          D.input({ className: 'pat-pickadate', ref: 'input1', value: value[0]})),
        D.span({ className: 'querystring-criteria-betweendt' }, 'to'),
        D.span({ className: 'querystring-date-wrapper'},
          D.input({ className: 'pat-pickadate', ref: 'input2', value: value[1]}))
      ]);
    }
  });

});
