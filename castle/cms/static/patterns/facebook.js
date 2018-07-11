/* global define */

define([
  'jquery',
  'pat-base',
  'castle-url/libs/script'
], function($, Base, $script) {
  'use strict';

  var FacebookPage = Base.extend({
    name: 'facebookpage',
    trigger: '.pat-facebookpage',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var self = this;

      if(window.FB){
        self.initialize();
      }else{
        $script('//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.5', function(){
          self.initialize();
        });
      }
    },
    initialize: function(){
      var self = this;
      FB.init({
        status: true,
        xfbml: true,
        version: 'v2.5'
      });
    }
  });

  return FacebookPage;

});
