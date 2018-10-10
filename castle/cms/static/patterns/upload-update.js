define([
  'jquery',
  'mockup-patterns-base',
  'castle-url/libs/react/react.min',
  'castle-url/components/add-content-modal',
  'mockup-utils',
], function($, Base, R, AddContentModal, utils) {
  'use strict';



  var UploadPattern = Base.extend({
    name: 'castleupload',
    trigger: '.pat-upload-update',
    parser: 'mockup',
    defaults: {},
    init: function () {
      var widget = $(this.$el);
      var content = widget.attr('content');
      var field = widget.attr('field');
      var data = [{
        update: true,
        content: content,
        field: field
      }]
      var uploadButton = widget.find('.file-upload-btn');
      var target = widget.find('.modal-target')[0];
      uploadButton.click(function() {
        var component = R.render(R.createElement(AddContentModal, data), target);
        $('.modal-backdrop').css('z-index', 'auto');
        $('.modal-content').css('margin-top', '100px');
      });
      var removeButton = widget.find('.file-remove-btn');
      removeButton.click(function() {
        if (confirm('Are you sure you want to remove this file?')) {
          var xhr = new XMLHttpRequest();
          var fd = new FormData();
          fd.append('action', 'remove');
          fd.append('content', content);
          fd.append('field', field);
          fd.append('_authenticator', utils.getAuthenticator());

          xhr.open('post', $('body').attr('data-portal-url') + '/@@content-creator');
          xhr.send(fd);

          location.reload(true);
        }
      })
    }
  });

  return UploadPattern

});
