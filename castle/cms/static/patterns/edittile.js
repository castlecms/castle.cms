/* global define */

define([
  'jquery',
  'pat-base',
  'mockup-patterns-modal',
  'mockup-utils'
], function($, Base, Modal, utils) {
  'use strict';

  var EditTile = Base.extend({
    name: 'edittile',
    trigger: '.pat-edittile',
    parser: 'mockup',
    defaults: {
      url: null,
      editUrl: null,
      label: 'Tile'
    },
    init: function() {
      var self = this;
      var $editBtn = $('<a href="' + self.options.editUrl + '" class="edit-tile">' + self.options.label + '</a>');

      $editBtn.click(function(e){
        utils.loading.show();
        e.preventDefault();
        $.ajax({
          type: "GET",
          url: self.options.editUrl,
          success: function(value, xhr) {
            utils.loading.hide();
            var modal = new Modal(self.$el, {
              html: value,
              loadLinksWithinModal: true,
              buttons: '.formControls > input[type="submit"], .actionButtons > input[type="submit"]'
            });
            modal.$el.off('after-render');
            modal.on('after-render', function() {
              $('input[name*="cancel"]', modal.$modal).off('click').on('click', function() {
                // Close overlay
                modal.hide();
              });
            });
            modal.show();
            modal.$el.off('formActionSuccess');
            modal.on('formActionSuccess', function (event, response, state, xhr) {
              window.location.reload();
            });
          }
        });
      });
      self.$el.append($editBtn);
    }
  });
  return EditTile;

});
