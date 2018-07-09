/* global define */

define([
  'jquery',
  'pat-base',
  'underscore'
], function($, Base, _) {
  'use strict';

  var _selectTemplate = '<div class="row previewselect-container">' +
  '<div class="col-md-6 input"></div>' +
  '<div class="col-md-6 preview"></div>' +
'</div>';

  var PreviewSelectPattern = Base.extend({
    name: 'previewselect',
    trigger: '.pat-previewselect',
    defaults: {
      previews: {}
    },
    parser: 'mockup',
    init: function() {
      var self = this;
      var $dom = $(_selectTemplate);
      var $parent = self.$el.parent();
      $parent.append($dom);
      $('.input', $dom).append(self.$el);

      var _change = function(){
        var val = self.$el.val();
        $('.preview', $dom).empty();
        if(self.options.previews[val]){
          $('.preview', $dom).append(
            '<div><h4>Preview</h4><img src="' +
              $('body').attr('data-portal-url') + '/' + self.options.previews[val] +
            '" /></div>');
        }
      };
      _change();
      self.$el.on('change', _change);
    }
  });

  return PreviewSelectPattern;

});
