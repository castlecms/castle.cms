define([
  'jquery',
  'mockup-patterns-base',
  'castle-url/libs/react/react.min',
  'castle-url/components/add-content-modal',
  'mockup-utils',
], function($, Base, R, AddContentModal, utils) {
  'use strict';

  var UploadPattern = Base.extend({
    name: 'upload-update',
    trigger: '.pat-upload-update',
    parser: 'mockup',
    defaults: {
      uid: null,
      tmp_field_id: null
    },

    bytesToSize: function(bytes) {
      var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      if (bytes == 0) return '0 Byte';
      var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
      return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    },

    updateReplacement: function(name, type, size){
      var $widget = $(this.$el);
      $widget.find('.new-value').remove();
      var $newValue = $('<p class="discreet new-value"/>');
      $widget.append($newValue);
      $newValue.html(name + '(' + type + '): ' + this.bytesToSize(size));
      var $replace = $widget.find('#form-widgets-file-replace');
      if($replace.size() === 0){
        // no file to start with, let's just add hidden input here...
        $replace = $('<input id="form-widgets-file-replace" name="form.widgets.file.action" type="hidden"/>')
        $widget.append($replace);
      }
      $replace.attr('value', JSON.stringify({
        replace: true,
        name: name,
        type: type,
        size: size,
        tmp_field_id: this.options.tmp_field_id
      }));
    },

    init: function () {
      var self = this;
      self.component = null;
      if(!self.options.tmp_field_id){
        self.tmp_field_id = 'tmp_' + utils.generateId();
      }

      var $widget = $(this.$el);

      var $replace = $widget.find('#form-widgets-file-replace');
      var existingValue = $replace.attr('value');
      if(existingValue && existingValue.indexOf('{') !== -1){
        // already had an existing value but error on form, update...
        try{
          var data = JSON.parse(existingValue);
          if(data.replace){
            self.updateReplacement(data.name, data.type, data.size);
            self.options.tmp_field_id = data.tmp_field_id;
          }
        }catch(e){
          // handle json issues
        }
      }
      $widget.find('#form-widgets-file-input').click(function(evt){
        evt.preventDefault();

        var $div = $('<div/>');
        $widget.append($div);

        var data = {
          update: true,
          content: self.options.uid,
          field: self.options.tmp_field_id,
          autoUpload: true,
          onUploadFinished: function(item, component){
            // do something here...
            var file = component.state.files[0];
            self.component.hide();
            $div.remove();
            $('.modal-backdrop').remove();
            $('body').removeClass('modal-open');
            $('#form-widgets-file').css('opacity', '0.2');

            self.updateReplacement(file.name, file.type, file.size);
          }
        };
        self.el = R.createElement(AddContentModal, data);
        self.component = R.render(self.el, $div[0]);
        $('.modal-backdrop').css('z-index', 'auto');
        $('.modal-content').css('margin-top', '100px');
      });
    }
  });

  return UploadPattern

});
