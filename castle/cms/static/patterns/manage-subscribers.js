/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'castle-url/libs/react/react.min',
], function($, Base, R) {
  'use strict';

  var SubscribersComponent = R.createClass({
    getDefaultProps: function() {
      portal_url: $('body').attr('data-portal-url'),
      data: JSON.parse($('.pat-subscribers').attr('data-pat-manage-subscribers'))
    }
    getInitialState: function() {
      this.props.data[]
      return {
        page: 1
      };
    },
    render: function(){
      return D.div({ className: 'castle-manage-subscribers'}, [
      ]);
    },
    getPage: function(pageNum){
      var url = this.portal_url + '/manage-subscribers?page=' + this.page
      $.ajax({
        url: url,
        success: function(result){

        },
        error: function(){
          
        }
      });
    }
  });

  var ManageSubscribers = Base.extend({
    name: 'manage-subscribers',
    trigger: '.pat-subscribers',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var that = this;
      var component = R.render(R.createElement(SubscribersComponent, that.options), that.$el[0], function(){
        if(document.body.className.indexOf('subscribers-initialized') === -1){
          document.body.className += ' subscribers-initialized';
        }
        $('body').trigger('subscribers-initialized', that, component);
      });
    },
  });

  return ManageSubscribers;

});
