/*
 * Copyright (c) 2014, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 *
 */

define([
  'jquery',
  'castle-url/addsite/dispatcher',
  'castle-url/libs/eventEmitter/EventEmitter.min',
  'castle-url/libs/object-assign'
], function($, Dispatcher, EventEmitter, assign){
  'use strict';

  var _data = {};
  var CHANGE_EVENT = 'change';

  /**
   * Create a TODO item.
   * @param  {string} text The content of the TODO
   */
  function add(id, data) {
    _data[id] = data;
  }

  /**
   * Update a TODO item.
   * @param  {string} id
   * @param {object} updates An object literal containing only the data to be
   *     updated.
   */
   function update(id, data) {
    _data[id] = data;
  }

  function fieldsetUpdate(id, parent, data){
    _data[parent][id] = data;
  }

  /**
   * Delete a TODO item.
   * @param  {string} id
   */
  function destroy(id) {
    delete _data[id];
  }

  var Store = assign({}, EventEmitter.prototype, {

    /**
     * get the initial data from the site provided data
     */
    initialize: function(data){
      _data = data;
    },

    /**
     * Get the entire collection of TODOs.
     * @return {object}
     */
    getAll: function() {
      return _data;
    },

    get: function(id){
      return _data[id];
    },

    add: function(id, data){
      add(id, data);
    },

    fieldsetUpdate: function(id, parent, data){
      fieldsetUpdate(id, parent, data);
    },

    update: function(id, data){
      update(id, data);
    },


    emitChange: function() {
      this.emit(CHANGE_EVENT);
    },

    /**
     * @param {function} callback
     */
    addChangeListener: function(callback) {
      this.on(CHANGE_EVENT, callback);
    },

    /**
     * @param {function} callback
     */
    removeChangeListener: function(callback) {
      this.removeListener(CHANGE_EVENT, callback);
    },

  });

  // Register callback to handle all updates
  Dispatcher.register(function(action) {
    switch(action.actionType) {
      case 'add':
        add(action.id, action.data);
        Store.emit('add', action.id);
        break;

      case 'update':
        update(action.id, action.data);
        Store.emit('update');
        break;

      case 'fieldsetUpdate':
        fieldsetUpdate(action.id, action.parent, action.data);
        Store.emit('update');
        break;

      case 'delete':
        destroy(action.id);
        Store.emit('delete', action.id);
        break;

      default:
        // no op
    }
  });
  return Store;
});
