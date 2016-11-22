define([
  'jquery',
  'castle-url/addsite/dispatcher'
], function($, Dispatcher) {
  'use strict';

  var Actions = {

    /**
     * @param  {string} text
     */
    create: function(text) {
      Dispatcher.handleViewAction({
        actionType: 'create',
        text: text
      });
    },

    /**
     * @param  {string} id
     */
    destroy: function(id) {
      Dispatcher.handleViewAction({
        actionType: 'destroy',
        id: id
      });
    },

    fieldsetUpdate: function(id, parent, value) {
      Dispatcher.handleViewAction({
        'actionType': 'fieldsetUpdate',
        'id': id,
        'data': value,
        'parent': parent
      });
    },

    update: function(id, value) {
      Dispatcher.handleViewAction({
        'actionType': 'update',
        'id': id,
        'data': value
      });
    },

  };

  return Actions;
});
