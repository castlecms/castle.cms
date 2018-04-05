/*
  Migrate to a pattern from https://github.com/jonom/jquery-focuspoint/blob/master/js/jquery.focuspoint.js

*/

define([
  'jquery',
  'pat-base',
  'mockup-utils'
], function($, Base, utils) {
  "use strict";

  var IMAGES_TO_WATCH_ON_SCROLL = {};
  var registerImageToWatch = function(pattern, scale){
    IMAGES_TO_WATCH_ON_SCROLL[utils.generateId()] = {
      pattern: pattern,
      scale: scale
    };
  };

  var _resize_timeout = 0;
  var _resize = function(){
    $('.focuspoint').each(function(){
      var pattern = $(this).data('pattern-focuspoint');
      if(pattern){
        pattern.adjustFocus();
      }
    });
  };
  $(window).on('resize', function(){
    if(_resize_timeout){
      clearTimeout(_resize_timeout);
    }
    _resize_timeout = setTimeout(_resize, 50);
  });

  $('body').on('toolbar-initialized', function(){
    _resize();
  });

  var _active = false;
  var _scroll = function(){
    _active = true;
    var remove = [];
    for(var uid in IMAGES_TO_WATCH_ON_SCROLL){
      var item = IMAGES_TO_WATCH_ON_SCROLL[uid];
      if(!item){
        continue;
      }
      var pattern = item.pattern;
      if(pattern.isVisible()){
        pattern._upgradeImage(item.scale);
        remove.push(uid);
      }
    }
    for(var i=0; i<remove.length; i++){
      delete IMAGES_TO_WATCH_ON_SCROLL[remove[i]];
    }
    _active = false;
  };

  $(window).on('scroll', function(){
    if(_active){
      return;
    }
    _scroll();
  });

  var FocusPoint = Base.extend({
    name: 'focuspoint',
    trigger: '.focuspoint',
    parser: 'mockup',
    defaults: {
      reCalcOnWindowResize: true,
  		throttleDuration: 17
    },

  	//Calculate the new left/top values of an image
  	calcShift: function(conToImageRatio, containerSize, imageSize, focusSize, toMinus) {
  		var containerCenter = Math.floor(containerSize / 2); //Container center in px
  		var focusFactor = (focusSize + 1) / 2; //Focus point of resize image in px
  		var scaledImage = Math.floor(imageSize / conToImageRatio); //Can't use width() as images may be display:none
  		var focus =  Math.floor(focusFactor * scaledImage);
  		if (toMinus){
        focus = scaledImage - focus;
      }
  		var focusOffset = focus - containerCenter; //Calculate difference between focus point and center
  		var remainder = scaledImage - focus; //Reduce offset if necessary so image remains filled
  		var containerRemainder = containerSize - containerCenter;
  		if (remainder < containerRemainder){
        focusOffset -= containerRemainder - remainder;
      }
  		if (focusOffset < 0){
        focusOffset = 0;
      }

  		return (focusOffset * -100 / containerSize)  + '%';
  	},

    manuallySetImageSize: function(){
      this.$el.data('imageW', this.image.naturalWidth);
      this.$el.data('imageH', this.image.naturalHeight);
    },

    detectNaturalSize: function(){
      var that = this;

      if(that.image.complete){
        that.manuallySetImageSize();
        that.adjustFocus();
      }

      that.$image.on('load', function(){
        that.manuallySetImageSize();
        that.adjustFocus();
      });
    },

  	//Re-adjust the focus
  	adjustFocus: function() {
      var that = this;
      var $el = this.$el;
      var imageW, imageH, scalesInfo, defaultScale;
      try{
        scalesInfo = JSON.parse($el.attr('data-scales-info'));
        defaultScale = $el.data('scale');
        var imageInfo = scalesInfo[defaultScale];
    		imageW = imageInfo.w;
    		imageH = imageInfo.h;
      }catch(e){
        // check for old style
        imageW = $el.data('imageW');
    		imageH = $el.data('imageH');
      }

      if(!imageW || !imageH){
        return that.detectNaturalSize();
      }

  		var containerW = $el.width();
  		var containerH = $el.height();
  		var focusX = parseFloat($el.data('focusX') || 0);
  		var focusY = parseFloat($el.data('focusY') || 0);

  		//Amount position will be shifted
  		var hShift = 0;
  		var vShift = 0;

  		if (!(containerW > 0 && containerH > 0 && imageW > 0 && imageH > 0)) {
  			return false; //Need dimensions to proceed
  		}

  		//Which is over by more?
  		var wR = imageW / containerW;
  		var hR = imageH / containerH;

  		//Reset max-width and -height
  		that.$image.css({
  			'max-width': '',
  			'max-height': ''
  		});

  		//Minimize image while still filling space
  		if (imageW > containerW && imageH > containerH) {
        var styleName = (wR > hR) ? 'max-height' : 'max-width';
  			that.$image.attr('style', styleName + ': 100% !important');
  		}

  		if (wR > hR) {
  			hShift = this.calcShift(hR, containerW, imageW, focusX);
  		} else if (wR < hR) {
  			vShift = this.calcShift(wR, containerH, imageH, focusY, true);
  		}

  		that.$image.css({
  			top: vShift,
  			left: hShift
  		});

      // check if we should upgrade the size
      if(scalesInfo && defaultScale && (containerW > imageW || containerH > imageH)){
        // we upgrade image to....
        // something as big as what will fit container but not bigger than it needs to be
        // attempt image upgrade...
        var targetScale = defaultScale;
        var upgradedH = imageH;
        var upgradedW = imageW;
        for(var scale in scalesInfo){
          var info = scalesInfo[scale];
          if((info.w > upgradedW || info.h > upgradedH) &&
             (upgradedW < containerW || upgradedH < containerH)){
            upgradedW = info.w;
            upgradedH = info.h;
            targetScale = scale;
          }
        }
        if(targetScale !== defaultScale){
          // okay, we can upgrade
          that.upgradeImage(targetScale);
        }
      }
  	},

    upgradeImage: function(scale){
      var that = this;
      if(that.isVisible()){
        return that._upgradeImage(scale);
      }
      registerImageToWatch(that, scale);
    },

    _upgradeImage: function(scale){
      var that = this;
      var baseUrl = that.$el.attr('data-base-url');
      var url = baseUrl + scale;
      var img = new Image();
      img.onload = function(){
        that.$image.attr('src', url);
        that.$el.data('scale', scale);
        that.adjustFocus();
      };
      img.src = url;
    },

    isVisible: function(){
      var docViewTop = $(window).scrollTop();
      var elemTop = this.$el.offset().top;
      return (docViewTop + $(window).height()) >= elemTop;
    },

    init: function() {
      var that = this;

      // manually set height if none set in css
      if(that.$el.height() < 5){
        var $el = that.$el.parent();
        while($el.height() < 5){
          $el = $el.parent();
        }
        that.$el.height($el.height());
      }
      that.$image = that.$el.find('img').first();
      that.image = that.$image[0];

      that.adjustFocus();
    }
  });

  return FocusPoint;

});
