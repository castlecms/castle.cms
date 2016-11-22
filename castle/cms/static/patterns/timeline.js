/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'castle-url/libs/script'
], function($, Base, $script) {
  'use strict';

  var TweetText = Base.extend({
    name: 'timeline',
    trigger: '.pat-timeline',
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
      twttr.widgets.createTimeline(
        self.options.widgetId,
        self.$el.get(0),
        self.options.parameters
      );
    }
  });

  return TweetText;

});
