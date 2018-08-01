/* global define */

define([
  'jquery',
  'pat-base',
  'underscore',
  'castle-url/libs/fullcalendar/dist/fullcalendar.min'
], function($, Base) {
  'use strict';

  var FullCalendarPattern = Base.extend({
    name: 'fullcalendar',
    trigger: '.pat-fullcalendar',
    defaults: {
    },
    parser: 'mockup',
    init: function() {
      var self = this;
      self.$el.fullCalendar(self.options);
    }
  });

  return FullCalendarPattern;

});
