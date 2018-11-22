/* global define */

define([
  'jquery',
  'pat-base',
], function($, Base) {
  'use strict';

  var ExistingContent = Base.extend({
    name: 'existing',
    trigger: '.pat-existing',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      this.loadContent();
    },
    loadContent: function() {
      var that = this;
      $('.pat-existing').each(function() {
        var main_content = $(this).attr('content_url') + ' #main-content';
        var has_recaptcha = $(this).attr('recaptcha');
        function check_recaptcha() {
          if (has_recaptcha === "True") {
            require(['https://www.google.com/recaptcha/api.js']);
          }
        }
        $(this).load(main_content, check_recaptcha);
      });
      that.loaded = true;
    }
  });

  return ExistingContent;

});
