
define([
  'jquery',
  'castle-url/libs/react/react.min'
], function($, R) {
  'use strict';

  var Class = function(bases, klass){
    /* poor mans class based system here.
       provide list of bases and they'll be merged.
       No super/etc provided, just overrided. */
    var _bases = [];
    bases.forEach(function(base){
      if(base.original_class){
        _bases.push(base.original_class);
      }else{
        _bases.push(base);
      }
    });
    var args = [true, {}].concat(_bases);
    args.push(klass);
    var merged_base = extend.apply(null, args);
    var _class = R.createClass(merged_base);
    _class.original_class = merged_base;
    return _class;
  };

  var extend = function(){
    var result = {};
    for(var i=0; i<arguments.length; i++){
      var other = arguments[i];
      for(var key in other){
        result[key] = other[key];
      }
    }
    return result;
  };

  var createModalComponent = function(Component, id, settings){
    if(settings === undefined){
      settings = {};
    }
    var el = document.getElementById(id);
    if(el){
      el.parentNode.removeChild(el);
    }
    var div = document.createElement('div');
    div.id = id;
    div.className = 'component-wrapper';
    document.body.appendChild(div);
    if(!settings.parent){
      settings.parent = this;
    }
    return R.render(R.createElement(Component, settings), div);
  };

  var BindComponentFactory = function(Component, SettingsFactory, settings){
    return function(el){
      if(settings === undefined){
        settings = {};
      }
      if(SettingsFactory){
        var newSettings = SettingsFactory(el);
        if(typeof(newSettings) === 'function'){
          // use callback to finish this...
          return newSettings(function(_settings){
            settings = $.extend({}, true, _settings, settings);
            return R.render(R.createElement(Component, settings), el);
          });
        }
        settings = $.extend({}, true, newSettings, settings);
      }
      return R.render(R.createElement(Component, settings), el);
    };
  };

  var BindComponentFactoryRoot = function(Component, SettingsFactory, id){
    /* binds to new element in body tag automatically */
    return function(settings){
      $('#' + id).remove();
      var $div = $('<div id="' + id + '" class="component-wrapper" />');
      $('body').append($div);
      return BindComponentFactory(Component, SettingsFactory, settings)($div[0]);
    };
  };

  return {
    Class: Class,
    createModalComponent: createModalComponent,
    extend: extend,
    BindComponentFactory: BindComponentFactory,
    BindComponentFactoryRoot: BindComponentFactoryRoot,
    getToolbarSettings: function(){
      var $el = $('.pat-castletoolbar,.castletoolbar-settings');
      if($el.length > 0){
        return JSON.parse($el.attr('data-pat-castletoolbar'));
      }
      return {};
    }
  };
});
