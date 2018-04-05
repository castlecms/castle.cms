/* global define */

define([
  'jquery',
  'pat-base',
], function($, Base) {
  'use strict';
  var SurveyInvite = Base.extend({
    name: 'survey',
    trigger: '.pat-survey',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var self = this;
      $('.pat-survey').append('<span>Invited to take a survey</span>')
    }
  });

  return SurveyInvite;

});
