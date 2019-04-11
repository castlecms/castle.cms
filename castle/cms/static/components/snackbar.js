/* global define */

define([
  'jquery',
  'castle-url/libs/react/react',
], function($, R) {
  'use strict';
  var D = R.DOM;

  var SnackbarComponent = R.createClass({
    getInitialState: function(){
      return {
        text: 'default'
      }
    },
    show: function(){
      var bar = document.getElementById("snackbar");
      bar.className = "show";
      setTimeout(function(){ bar.className = bar.className.replace("show", ""); }, 3000);
    },
    setText: function(message){
      this.setState({
        text: message
      })
    },
    showText: function(message){
      this.setText(message);
      this.show();
    },
    render: function(){
      var that = this;
      return D.div({
        id: "snackbar"
      }, that.state.text);
    }
  });

  return SnackbarComponent
});
