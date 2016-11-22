define([
  'castle-url/libs/dispatcher',
  'castle-url/libs/eventEmitter/EventEmitter.min',
  'castle-url/libs/object-assign',
  'castle-url/components/utils'
], function(Dispatcher, EventEmitter, assign, cutils) {
  'use strict';

  var Store = assign({}, EventEmitter.prototype, {

    data: null,
    initialize: function(){
      this.data = {
        sortOn: '',
        reversed: false,
        criterias: []
      };
    },

    setData: function(data){
      this.data = data;
    },

    getData: function(){
      return this.data;
    },

    getAllCriterias: function() {
      return this.data.criterias || [];
    },

    getCriteria: function(idx){
      return this.data.criterias[idx];
    },

    addCriteria: function(data){
      if(!this.data.criterias){
        this.data.criterias = [];
      }
      this.data.criterias.push(data);
    },

    update: function(data){
      var changes = false;
      if(data.sortOn !== this.data.sortOn || data.reversed !== this.data.reversed){
        changes = true;
      }
      this.data = cutils.extend(this.data, data);
      return changes;
    },

    updateCriteria: function(idx, data){
      if(!this.data.criterias || !this.data.criterias[idx]){
        return;
      }
      var changes = false;
      var original = this.data.criterias[idx];
      for(var key in data){
        if(original[key] !== data[key]){
          changes = true;
        }
      }
      this.data.criterias[idx] = cutils.extend(this.data.criterias[idx], data);
      return changes;
    },

    removeCriteria: function(idx){
      if(!this.data.criterias || !this.data.criterias[idx]){
        return;
      }
      this.data.criterias.splice(idx, 1);
    },

    /**
     * @param {function} callback
     */
    addChangeListener: function(event, callback) {
      this.on(event, callback);
    },

    /**
     * @param {function} callback
     */
    removeChangeListener: function(event, callback) {
      this.removeListener(event, callback);
    }

  });


  return function(){
    var store = assign({}, Store);
    var dispatcher = new Dispatcher();
    store.initialize();

    // Register callback to handle all updates
    dispatcher.register(function(action) {
      switch(action.actionType) {
        case 'addCriteria':
          store.addCriteria(action.data);
          store.emit('change', action);
          break;

        case 'updateCriteria':

          if(store.updateCriteria(action.idx, action.data) || action.force){
            store.emit('change', action);
          }
          break;

        case 'removeCriteria':
          store.removeCriteria(action.idx);
          store.emit('change', action);
          break;

        case 'update':
          if(store.update(action.data)){
            store.emit('change', action);
          }
          break;

        default:
          // no op
      }
    });
    return {
      store: store,
      dispatcher: dispatcher
    };
  };

});
