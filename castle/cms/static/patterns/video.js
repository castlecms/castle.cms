/* global define */

define([
  'jquery',
  'pat-base',
  'underscore',
  'castle-url/libs/mediaelement/build/mediaelement-and-player'
], function($, Base, _) {
  'use strict';

  var VideoPattern = Base.extend({
    name: 'video',
    trigger: '.pat-video',
    parse: 'mockup',
    defaults: {
    },
    init: function() {
      var self = this;
      if(self.$el.attr('controls') === undefined){
        self.applyClickControls();
      }else{
        self.$el.mediaelementplayer({
        });
      }
    },
    applyClickControls: function(){
      var that = this;
      that.$el.on('click', function(){
        if(this.paused){
          this.play();
        }else{
          this.pause();
        }
      });
    }
  });

  return VideoPattern;

});
