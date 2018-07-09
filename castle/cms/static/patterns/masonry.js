/* global define */

define([
  'jquery',
  'pat-base',
  'underscore',
  'castle-url/libs/masonry.min',
  'castle-url/libs/imagesloaded'
], function($, Base, _, Masonry) {
  'use strict';

  var bool = function(val){
    if(typeof(val) === 'boolean'){
      return val;
    }
    val = val.lower();
    if(val == 't' || val == 'true' || val == '1'){
      return true;
    }
    return false;
  };

  var MasonryPattern = Base.extend({
    name: 'masonry',
    trigger: '.pat-masonry',
    parser: 'mockup',
    defaults: {
      itemSelector: '.grid-item'
    },
    types: {
      columnWidth: parseInt,
      gutter: parseInt,
      percentPosition: bool,
      fitWidth: parseInt,
      originLeft: parseInt,
      originTop: parseInt
    },
    init: function() {
      var self = this;
      for(var name in self.options){
        if(self.types[name]){
          self.options[name] = self.types(self.options[name]);
        }
      }
      self.masonry = new Masonry( self.$el[0], this.options);
      self.masonry.on('layoutComplete', function(items) {
        var counts = {};
        items.forEach(function(item){
          var el = item.element;
          if(el.originalClassName){
            el.className = el.originalClassName;
          }
          el.originalClassName = el.className;
          var $el = $(el);
          var left = $el.css('left');
          left = left.replace('px', '');
          var className = 'msn' + left[0];
          left.substr(1).split('').forEach(function(){
            className += '0';
          });
          if(!counts[className]){
            counts[className] = 0;
          }
          counts[className] += 1;
          $el.addClass(className).addClass(className + 'I' + counts[className])
             .addClass('I' + counts[className]).addClass('layout-finished');
        });
      });
      if($('img', self.$el).size() > 0){
        self.$el.imagesLoaded().progress(function(){
          self.masonry.layout();
        });
      }else{
        self.masonry.layout();
      }
    },
    addItems: function($items){
      var self = this;
      self.masonry.appended($items.toArray());
      $items.imagesLoaded().progress(function(){
        self.masonry.layout();
      });
    }
  });

  return MasonryPattern;

});
