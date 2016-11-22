/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/script'
], function($, Base, _, $script) {
  'use strict';

  var TweetText = Base.extend({
    name: 'tweettext',
    trigger: '.pat-tweettext',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var self = this;

      if(window.twttr){
        self.initialize();
      }else{
        $script('https://platform.twitter.com/widgets.js', function(){
          self.initialize();
        });
      }
    },
    initialize: function(){
      var self = this;
      var settings = self.options.settings;

      twttr.widgets.createTweet(
        self.options.tweetID,
        self.$el.get(0),
        settings
      );
    }
  });

  return TweetText;

});
