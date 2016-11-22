/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/leaflet-dist/leaflet'
], function($, Base, _, L) {
  'use strict';

  var Map = Base.extend({
    name: 'map',
    trigger: '.pat-map',
    parser: 'mockup',
    defaults: {
      markers: [],
      center: null, // should be provided as a string
      initialZoom: 10,
      height: 200
    },
    init: function() {
      L.Icon.Default.imagePath = $('body').attr('data-portal-url') + '/++plone++castle/libs/leaflet-dist/images';
      var self = this;
      var id = self.$el.attr('id');
      if(!id){
        // generate random id for it
        id = 'mapid' + Math.floor(Math.random()*999999);
        self.$el.attr('id', id);
      }
      if(typeof self.options.markers === 'string'){
        self.options.markers = $.parseJSON(self.options.markers);
      }
      if(typeof self.options.center === 'string'){
        self.options.center = $.parseJSON(self.options.center);
      }
      self.$el.height(self.options.height);
      var center = self.options.center;
      var markers = self.options.markers;
      if(!center){
        if(markers.length > 0){
          center = markers[0];
        }
      }
      if(!center){
        center = {lat: 0, lng: 0};
      }

      self.map = L.map(self.$el[0], {
        scrollWheelZoom: false
      }).setView([center.lat, center.lng], self.options.initialZoom);
      L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(self.map);

      _.each(markers, function(marker){
        if(!marker){
          return;
        }
        var markerObj = L.marker([marker.lat, marker.lng]).addTo(self.map);
        if(marker.popup){
          markerObj.bindPopup(marker.popup);
        }
      });
    }
  });

  return Map;

});
