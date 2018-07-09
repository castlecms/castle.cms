/* global define */

define([
  'jquery',
  'mockup-patterns-base',
], function($, Base) {
  'use strict';

  var Subscription = Base.extend({
    name: 'subscribe',
    trigger: '.pat-subscribe',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var self = this;

      self.setupForm();
    },
    setupForm: function() {
      var self = this;
      self.$form = self.$el.find('form');
      self.url = self.$form.attr('action');

      self.$form.submit(function(e) {
        e.preventDefault();

        self.$form.ajaxSubmit({
          type: 'POST',
          url: self.url,
          data: {
            'form.buttons.subscribe': 'subscribe'
          },
          failure: function(data) {
            alert("There was a problem while submitting your subscription.");
            console.log('Subscribe attempt failed: ' + data);
          },
          success: function(responseText, statusText, xhr) {
            self.$el.find('.portalMessage').remove();
            var message = $('.portalMessage', responseText);
            var form = $('form', responseText);

            $('.documentFirstHeading', self.$el).append(message);
            $('form', self.$el).replaceWith(form);

            //When we get a valid submit, the form
            //"Disappears" off the top of the viewport sometimes
            var formTop = self.$el.find('h1').offset().top;
            $('body').scrollTop(formTop);

            //We replaced the form, so reset the submit handler
            self.setupForm();
          },
        });
      });
    }
  });

  return Subscription;

});
