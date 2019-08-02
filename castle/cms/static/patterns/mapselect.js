/* global define, alert */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'pat-registry',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/modal',
  'castle-url/components/utils',
  'mockup-patterns-tinymce',
  'pat-mockup-parser',
  'castle-url/libs/script'
], function($, Base, _, registry, R, utils, Modal, component_utils, TinyMCE, Parser, $script) {
  'use strict';

  var D = R.DOM;

  var generateColorDropdown = function(selected) {
    var colorList = { Red: '#e6194b', Green: '#3cb44b', Yellow: '#ffe119', Blue: '#0082c8', Orange: '#f58231', Purple: '#911eb4', Cyan: '#46f0f0', Magenta: '#f032e6', Lime: '#d2f53c', Pink: '#fabebe', Teal: '#008080', Lavender: '#e6beff', Brown: '#aa6e28', Beige: '#fffac8', Maroon: '#800000', Mint: '#aaffc3', Olive: '#808000', Coral: '#ffd8b1', Navy: '#000080', Grey: '#808080', White: '#FFFFFF', Black: '#000000'};
    var color_keys = Object.keys(colorList);
    return [
      D.label({}, 'Color'),
      D.select({
        ref: 'color',
        defaultValue: selected,
        className: 'input-group'},[
          color_keys.map(function(name) {
            var color = colorList[name];
            return D.option({
              value: color }, name);
          })
        ])
    ];
  };

  var getLat = function(data){
    return (data.geometry.location.lat && data.geometry.location.lat()) || data.geometry.location.G;
  };
  var getLng = function(data){
    return (data.geometry.location.lng && data.geometry.location.lng()) || data.geometry.location.K;
  };
  var formatEntry = function(address, lat, lng){
    if(!lat || !lng){
      return 'No point selected';
    }
    return address + '(' + lat.toFixed(6) + ',' + lng.toFixed(6) + ')';
  };

  var MapSearchComponent = R.createClass({
    getInitialState: function(){
      return {
        results: [],
        searchTerm: '',
        searched: false,
        selected: -1
      };
    },
    searchClicked: function(e){
      if(e){
        e.preventDefault();
      }
      var that = this;
      utils.loading.show();
      var geocoder = new window.google.maps.Geocoder();
      geocoder.geocode({ 'address': that.state.searchTerm }, function (results) {
        utils.loading.hide();
        that.setState({
          results: results,
          searched: true,
          selected: -1
        });
      });
    },
    searchInput: function(e){
      this.setState({
        searchTerm: e.target.value
      });
    },
    selectItem: function(idx, e){
      e.preventDefault();
      this.setState({
        selected: idx
      });
    },
    searchInputKeyPress: function(e){
      /* purpose here is to be able to use the enter key
         to go to next page in form */
      if((e.charCode || e.keyCode) === 13){
        this.searchClicked();
      }
    },
    render: function(){
      var that = this;
      var results = '';
      if(that.state.searched){
        if(that.state.results.length > 0){
          results = D.div({}, [
            D.p({ className: 'discreet'}, 'Select item from results'),
            D.ul({ className: 'castle-map-search-results'}, that.state.results.map(function(item, idx){
              var className = '';
              if(idx === that.state.selected){
                className = 'selected glyphicon glyphicon-ok';
              }
              var formatted = formatEntry(item.formatted_address, getLat(item), getLng(item));
              return D.li({className: className}, [
                D.a({ href: '#', onClick: that.selectItem.bind(that, idx)}, formatted)
              ]);
            }))
          ]);
        }else{
          results = 'No results';
        }
      }
      return D.div({ className: 'map-search-container'}, [
        D.div({ className: 'form-group'}, [
          D.label({}, 'Search Location'),
          D.div({ className: 'input-group'}, [
            D.input({type: "text", placeholder: 'Location', className: 'form-control',
                     value: that.state.searchTerm, onChange: that.searchInput,
                     onKeyDown: that.searchInputKeyPress}),
            D.span({ className: "input-group-btn"},
              D.button({ className: "plone-btn plone-btn-primary", type: "button",
                         onClick: that.searchClicked }, 'Search')
            )
          ])
        ]),
        results
      ]);
    }
  });

  var MapperAddMarkerComponent = component_utils.Class([Modal], {
    getInitialState: function(){
      return {
        customIcon: false
      };
    },
    addButtonClicked: function(e){
      e.preventDefault();
      var search = this.refs.search;
      var icon = this.getIcon();
      if(search.state.selected !== -1){
        var data = search.state.results[search.state.selected];
        var marker = {
          formatted: data.formatted_address,
          lat: getLat(data),
          lng: getLng(data),
          popup: this.props.tiny.tiny.getContent()
        };
        if( icon ) {
          marker.icon = icon;
        }
        this.props.parent.add(marker);
        this.hide();
      }else{
        alert('You have not selected a location');
      }
    },
    componentDidMount: function(){
      Modal.componentDidMount.apply(this);
      var $el = $(this.refs.tiny.getDOMNode());
      var options = $.extend({}, true, Parser.getOptions($el, 'tinymce'), {
        tiny: {
          height: 100
        }
      });
      this.props.tiny = new TinyMCE($el, options);
    },
    getIcon: function() {
      if( this.state.customIcon ) {
        return {
          'color': this.refs.color.getDOMNode().value,
          'iconText': this.refs.iconText.getDOMNode().value
        };
      }else{
        return false;
      }
    },
    renderContent: function(){
      var that = this;
      return D.div({ className: 'castle-markers-container'}, [
        R.createElement(MapSearchComponent, {parent: that, ref: 'search'}),
        D.div({ className: 'form-group'}, [
          D.label({}, 'Custom Icon'),
          D.input({
            type: 'checkbox',
            onClick: function(){
              that.setState({
                customIcon: !that.state.customIcon
              });
            }
          })
        ]),
        this.renderCustomIconForm(),
        D.div({ className: 'form-group'}, [
          D.label({}, 'Text'),
          D.textarea({ ref: 'tiny' })
        ])
      ]);
    },
    renderCustomIconForm: function() {
      if( this.state.customIcon) {
        return D.div({ className: 'form-group'}, [
          generateColorDropdown(false),
          D.label({}, 'Label'),
          D.input({ref: 'iconText',  'className': 'input-group'})
        ]);
      }else{
        return [];
      }
    },
    renderFooter: function(){
      var buttons = [D.button({
        type: 'button', className: 'btn btn-default small',
        onClick: this.addButtonClicked }, 'Add')];
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'add-marker-modal',
        title: 'Add Marker'
      });
    }
  });

  var MapperEditMarkerComponent = component_utils.Class([Modal], {
    getInitialState: function(){
      var icon = false;
      if( this.props.icon != false ) {
        icon = true;
      }
      return {
        customIcon: icon
      };
    },
    saveButtonClicked: function(e){
      e.preventDefault();
      this.hide();
      var popup = this.props.tiny.tiny.getContent();
      var icon = false;
      if( this.refs.color !== undefined ) {
        icon = {
          color: this.refs.color.getDOMNode().value,
          iconText: this.refs.iconText.getDOMNode().value
        };
      }

      this.props.callback(popup, icon);
    },
    componentDidMount: function(){
      Modal.componentDidMount.apply(this);
      var $el = $(this.refs.tiny.getDOMNode());
      var options = $.extend({}, true, Parser.getOptions($el, 'tinymce'), {
        tiny: {
          height: 100
        }
      });
      this.props.tiny = new TinyMCE($el, options);
    },
    renderCustomIconForm: function() {
      if( this.state.customIcon ) {
        return D.div({ className: 'form-group'}, [
          generateColorDropdown(this.props.icon.color),
          D.label({}, 'Label'),
          D.input({
            ref: 'iconText',
            className: 'input-group',
            defaultValue: this.props.icon.iconText
          })
        ]);
      }else{
        return [];
      }
    },
    renderContent: function(){
      var that = this;
      return D.div({ className: 'castle-edit-marker-container-container'}, [
        D.div({ className: 'form-group'}, [
          D.div({ className: 'form-group'}, [
            D.label({}, 'Custom Icon'),
            D.input({
              type: 'checkbox',
              checked: this.state.customIcon,
              onClick: function(){
                that.setState({
                  customIcon: !that.state.customIcon
                });
              }
            })
          ]),
          this.renderCustomIconForm(),
          D.label({}, 'Text'),
          D.textarea({ ref: 'tiny', value: this.props.data })
        ])
      ]);
    },
    renderFooter: function(){
      var buttons = [D.button({
        type: 'button', className: 'btn btn-default small',
        onClick: this.saveButtonClicked }, 'Save')];
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'edit-marker-modal',
        title: 'Edit Marker'
      });
    }
  });

  var MarkersComponent = R.createClass({
    addMarkerClicked: function(e){
      e.preventDefault();
      component_utils.createModalComponent(
        MapperAddMarkerComponent, 'castle-add-marker-modal', {
          parent: this
        });
    },
    add: function(data){
      this.props.value.push(data);
      this.forceUpdate();
      this.props.el.value = JSON.stringify(this.props.value);
    },
    removeClicked: function(idx, e){
      e.preventDefault();
      this.props.value.splice(idx, 1);
      this.forceUpdate();
      this.props.el.value = JSON.stringify(this.props.value);
    },
    editClicked: function(idx, e){
      e.preventDefault();
      var that = this;
      var marker = this.props.value[idx];
      component_utils.createModalComponent(
        MapperEditMarkerComponent, 'castle-add-marker-modal', {
          parent: this,
          data: marker.popup,
          icon: marker.icon || false,
          callback: function(popup, icon){
            marker.popup = popup;
            if( icon !== false ) {
              marker.icon = icon;
            }else{
              delete marker.icon;
            }
            that.forceUpdate();
            that.props.el.value = JSON.stringify(that.props.value);
          }
        });
    },
    render: function(){
      var that = this;
      var noMarkers = '';
      if(that.props.value.length === 0){
        noMarkers = D.p({ className: 'discreet'}, 'Currently no custom markers set');
      }
      return D.div({className: 'markers-container'}, [
        noMarkers,
        D.ul({}, that.props.value.map(function(marker, idx){
          return D.li({}, [
            D.span({ className: 'marker-label' }, marker.formatted),
            D.a({ href: '#', className: 'plone-btn plone-btn-default plone-btn-xs',
                  onClick: that.editClicked.bind(that, idx)}, 'Edit'),
            D.a({ href: '#', className: 'plone-btn plone-btn-warning plone-btn-xs',
                  onClick: that.removeClicked.bind(that, idx)},
              D.span({ className: 'glyphicon glyphicon-trash'}, 'Remove')),
          ]);
        })),
        D.a({href:'#', className:'plone-btn plone-btn-default plone-btn-sm',
             onClick: that.addMarkerClicked }, 'Add Marker')
      ]);
    }
  });

  var MapperSetPointComponent = component_utils.Class([Modal], {
    getInitialState: function(){
      return {
      };
    },
    addButtonClicked: function(e){
      e.preventDefault();
      var search = this.refs.search;
      if(search.state.selected !== -1){
        var data = search.state.results[search.state.selected];
        var state = null;
        var city = null;
        for (var i=0;i<data['address_components'].length;i++){
          var component = data['address_components'][i];
          if (component['types'].indexOf('administrative_area_level_1') >= 0){
            state = component['short_name'];
          } else if (component['types'].indexOf('locality') >= 0) {
            city = component['long_name'];
          }
        }
        this.props.parent.set({
          formatted: data.formatted_address,
          lat: (data.geometry.location.lat && data.geometry.location.lat()) || data.geometry.location.G,
          lng: (data.geometry.location.lng && data.geometry.location.lng()) || data.geometry.location.K,
          city: city,
          state: state
        });
        this.hide();
      }else{
        alert('You have not selected a location');
      }
    },
    renderContent: function(){
      var that = this;
      return D.div({ className: 'castle-markers-container'}, [
        R.createElement(MapSearchComponent, {parent: that, ref: 'search'})
      ]);
    },
    renderFooter: function(){
      var buttons = [D.button({
        type: 'button', className: 'btn btn-default small',
        onClick: this.addButtonClicked }, 'Set')];
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'set-center-point-modal',
        title: 'Set Center Point'
      });
    }
  });

  var CenterPointComponent = R.createClass({
    setPointClicked: function(e){
      e.preventDefault();
      component_utils.createModalComponent(
        MapperSetPointComponent, 'castle-add-center-modal', {
          parent: this
        });
    },
    set: function(data){
      this.props.value = data;
      this.props.el.value = JSON.stringify(data);
      this.forceUpdate();
    },
    render: function(){
      var that = this;
      var value = '';
      if(that.props.value){
        value = D.p({ className: 'discreet'},
          formatEntry(that.props.value.formatted, that.props.value.lat, that.props.value.lng));
      }
      return D.div({className: 'markers-container'}, [
        value,
        D.a({href:'#', className:'btn btn-default',
             onClick: that.setPointClicked }, 'Set point')
      ]);
    }
  });

  var PointsComponent = R.createClass({
    addPointClicked: function(e){
      e.preventDefault();
      component_utils.createModalComponent(
        MapperSetPointComponent, 'castle-add-center-modal', {
          parent: this
        });
    },
    set: function(data){
      if(!this.props.value){
        this.props.value = [];
      }
      this.props.value.push(data);
      this.props.el.value = JSON.stringify(this.props.value);
      this.forceUpdate();
    },
    removePoint: function(idx, e){
      e.preventDefault();
      this.props.value.splice(idx, 1);
      this.props.el.value = JSON.stringify(this.props.value);
      this.forceUpdate();
    },
    render: function(){
      var that = this;
      var value = that.props.value || [];
      var entries = [];

      value.forEach(function(item, idx){
        entries.push(D.li({ className: 'discreet', style: { display: 'block'}, key: 'map-entry-' + idx}, [
          formatEntry(item.formatted, item.lat, item.lng),
          ' - (',
          D.a({ href: '#', onClick: that.removePoint.bind(that, idx)}, 'Remove'),
          ')'
        ]));
      });
      return D.div({className: 'markers-container'}, [
        D.ul({}, entries),
        D.br({}, ''),
        D.a({href:'#', className:'btn btn-default',
             onClick: that.addPointClicked }, 'Add location')
      ]);
    }
  });


  var MapSelect = Base.extend({
    name: 'mapselect',
    trigger: '.pat-mapselect',
    parser: 'mockup',
    defaults: {
      type: 'markers'
    },
    init: function() {
      var self = this;

      if(window.google && window.google.maps){
        self.initialize();
      }else{
        var mapApiUrl = 'https://maps.google.com/maps/api/js?v=3&sensor=false';
        var apiKey = $('body').attr('data-google-maps-api-key');
        if(apiKey){
          mapApiUrl += '&key=' + apiKey;
        }
        $script(mapApiUrl, function(){
          self.initialize();
        });
      }
    },
    initialize: function(){
      var self = this;
      self.val = $.parseJSON(self.$el.val());
      self.$el.hide();
      var el = document.createElement('div');
      self.$el.parent().append(el);
      if(self.options.type === 'markers'){
        R.render(R.createElement(MarkersComponent, {
          el: self.$el[0],
          value: self.val || []
        }), el);
      }else if(self.options.type === 'point'){
        R.render(R.createElement(CenterPointComponent, {
          el: self.$el[0],
          value: self.val || {}
        }), el);
      }else if(self.options.type === 'points'){
        var val = self.val;
        if(val && val.lat && val.lng){
          // try to convert
          val = [val];
        }
        if(!val){
          val = [];
        }
        R.render(R.createElement(PointsComponent, {
          el: self.$el[0],
          value: val
        }), el);
      }
    }
  });

  return MapSelect;
});
