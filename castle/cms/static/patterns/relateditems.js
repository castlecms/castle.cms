/* Related items pattern.
 *
 * Options:
 *    vocabularyUrl(string): This is a URL to a JSON-formatted file used to populate the list (null)
 *    attributes(array): This list is passed to the server during an AJAX request to specify the attributes which should be included on each item. (['UID', 'Title', 'portal_type', 'path'])
 *    maximumSelectionSize(integer): The maximum number of items that can be selected in a multi-select control. If this number is less than 1 selection is not limited. (-1)
 *    selectableTypes(array): If the value is null all types are selectable. Otherwise, provide a list of strings to match item types that are selectable. (null)
 *    separator(string): Select2 option. String which separates multiple items. (',')
 *    tokenSeparators(array): Select2 option, refer to select2 documentation.
 *    ([",", " "])
 *    width(string): Specify a width for the widget. ('100%')
 *
 */


define([
  'jquery',
  'castle-url/libs/react/react.min',
  'underscore',
  'pat-base',
  'mockup-patterns-select2',
  'mockup-utils',
  'mockup-patterns-tree',
  'translate',
  'castle-url/components/content-browser',
  'castle-url/components/add-content-modal',
  'castle-url/components/utils'
], function($, R, _, Base, Select2, utils, Tree, _t,
            ContentBrowserComponent, AddContentModal, cutils) {
  'use strict';

  var D = R.DOM;

  var Select2ResultTemplate = _.template(
'<div class="pattern-relateditems-result  <% if (selected) { %>pattern-relateditems-active<% } %>">' +
'  <a href="#" class=" pattern-relateditems-result-select <% if (selectable) { %>selectable<% } %>">' +
'    <% if (typeof getIcon !== "undefined" && getIcon) { %><img src="<%- getURL %>/@@images/image/icon "> <% } %>' +
'    <span class="pattern-relateditems-result-title  <% if (typeof review_state !== "undefined") { %> state-<%- review_state %> <% } %>  " /span>' +
'    <span class="pattern-relateditems contenttype-<%- portal_type.toLowerCase() %>"><%- Title %></span>' +
'    <span class="pattern-relateditems-result-path"><%- path %></span>' +
'  </a>' +
'</div>');

  var RelatedItemsComponent = R.createClass({
    getInitialState: function(){
      return {
        selected: this.props.initial_selection,
        items: []
      };
    },

    getDefaultProps: function(){
      return {
        initial_selection: [],
        allowAdd: true,
        noItemsSelectedText: 'No items selected',
        portal_url: $('body').attr('data-portal-url')
      };
    },

    getQueryHelper: function(){
      var query = new utils.QueryHelper({
        vocabularyUrl: this.props.vocabularyUrl,
        batchSize: 30,
        pattern: this.props.parent,
        sort_on: 'getObjPositionInParent',
        sort_order: 'ascending',
        baseCriteria: this.props.baseCriteria.slice(),
        attributes: ['UID', 'Title', 'portal_type', 'path', 'review_state', 'is_folderish']
      });
      // get current path instead?
      // query.currentPath = '/';
      return query;
    },

    selectionUpdated: function(){
      this.props.updateValue(this.state.selected);
      this.load();
    },

    componentDidMount: function(){
      this.load();
      this.setupSelect2();
    },

    setupSelect2: function(){
      var that = this;
      var qh = new utils.QueryHelper({
        vocabularyUrl: this.props.vocabularyUrl,
        batchSize: 15,
        attributes: ['UID', 'Title', 'portal_type', 'path', 'review_state', 'is_folderish']
      });

      var ajax = qh.selectAjax();
      ajax.data = function(term, page){
        // override because we do not want sorting...
        var data = {
          query: JSON.stringify({
            criteria: qh.getCriterias(term)
          }),
          attributes: JSON.stringify(qh.options.attributes)
        };
        if (page) {
          data.batch = JSON.stringify(qh.getBatch(page));
        }
        return data;
      };
      ajax.quietMillis = 300;

      $(that.refs.select2.getDOMNode()).select2({
        placeholder: 'Type to search',
        minimumInputLength: 3,
        ajax: ajax,
        multiple: true,
        width: that.props.widget || 400,
        formatResult: function(item){
          item.selected = that.state.selected.indexOf(item.UID) !== -1;
          if (that.props.selectableTypes === null) {
            item.selectable = true;
          } else {
            item.selectable = _.indexOf(
              that.props.selectableTypes, item.portal_type) > -1;
          }
          var result = $(Select2ResultTemplate(item));
          result.on('click', function(){
            that.addSelection([item.UID]);
          });
          return result;
        }
      });
    },

    addSelection: function(selection){
      var that = this;
      var valid = [];
      selection.forEach(function(item){
        if(that.state.selected.indexOf(item) === -1){
          valid.push(item);
        }
      });
      if(that.props.maximumSelectionSize === 1){
        if(valid.length > 0){
          that.state.selected = [valid[0]];
        }
      }else{
        that.state.selected = that.state.selected.concat(valid);
      }
      that.selectionUpdated();
    },

    load: function(){
      var that = this;
      // load current selection...
      if(this.state.selected.length === 0){
        this.setState({
          items: []
        });
        return;
      }
      utils.loading.show();

      var criteria  = [{
        i: 'UID',
        o: 'plone.app.querystring.operation.list.contains',
        v: that.state.selected
      }];
      var method = 'GET';
      if(that.state.selected.length > 60){
        method = 'POST';
      }
      $.ajax({
        url: that.props.vocabularyUrl,
        dataType: 'JSON',
        type: method,
        data: {
          query: JSON.stringify({ criteria: criteria }),
          attributes: JSON.stringify([
            'Title', 'getURL', 'UID', 'id', 'path', 'portal_type',
            'review_state', 'is_folderish'
          ]),
          batch: JSON.stringify({
            page: 1,
            size: 500 // unlimited size here...
          })
        }
      }).done(function(data){
        // need to sort the results...
        var results = _.sortBy(data.results, function(item){
          return that.state.selected.indexOf(item.UID);
        });
        that.setState({
          items: results
        });
        if(that.props.input){
          $(that.props.input).trigger('loaded');
        }
      }).always(function(){
        utils.loading.hide();
      }).fail(function(){
        alert('error loading selection data');
      });
    },

    browseClicked: function(e){
      var that = this;
      e.preventDefault();

      var multiple = false;
      if(this.props.multiple && this.props.maximumSelectionSize !== 1){
        multiple = true;
      }
      var qh = that.getQueryHelper();
      var ContentBrowserBinder = cutils.BindComponentFactoryRoot(
        ContentBrowserComponent, function(){
          return {
            onSelectItem: function(item){
              that.addSelection([item.UID]);
            },
            onSelectItems: function(items){
              var uids = [];
              items.forEach(function(item){
                uids.push(item.UID);
              });
              that.addSelection(uids);
            },
            baseCriteria: qh.options.baseCriteria,
            query: qh,
            multiple: multiple,
            selectableTypes: that.props.selectableTypes
          };
        }, 'content-browser-react-container');

      var component = ContentBrowserBinder({});
      var newPath;
      if(that.props.selectableTypes && that.props.selectableTypes.length === 1){
        if(that.props.selectableTypes[0] === 'Image'){
          newPath = '/image-repository';
        }
        if(that.props.selectableTypes[0] === 'File'){
          newPath = '/file-repository';
        }
        if(that.props.selectableTypes[0] === 'Video'){
          newPath = '/video-repository';
        }
        if(that.props.selectableTypes[0] === 'Audio'){
          newPath = '/audio-repository';
        }
      }
      if(newPath){
        component.setPath(newPath);
        component.load();
      }
    },

    addClicked: function(e){
      var that = this;
      e.preventDefault();

      var tbarSettings = cutils.getToolbarSettings();

      var component = cutils.createModalComponent(AddContentModal, 'add-modal-react-container', {
        types: tbarSettings.add.types,
        allowEditAfterCreation: false,
        afterCreationCallback: function(data, component){
          that.addSelection([data.uid]);
          var $modal = component.getModalEl();
          $modal.modal('hide');
        },
        onHidden: function(e, component){
          var upload = component.refs.tab;
          if(upload && upload.state.files){
            var uids = [];
            _.each(upload.state.files, function(file){
              var listing = upload.refs[file.uid];
              if(listing.state.state === 'finished'){
                uids.push(listing.state.uid);
              }
            });
            that.addSelection(uids);
          }
        }
      });

      if(that.props.selectableTypes && (
          that.props.selectableTypes.indexOf('Image') !== -1 ||
          that.props.selectableTypes.indexOf('File') !== -1)){
        component.setState({selected: 'upload'});
      }
    },

    removeClicked: function(item, e){
      var that = this;
      e.preventDefault();
      var index = that.state.selected.indexOf(item.UID);
      if(index !== -1){
        that.state.selected.splice(index, 1);
      }
      that.selectionUpdated();
    },

    move: function(item, delta, e){
      var that = this;
      e.preventDefault();
      var index = that.state.selected.indexOf(item.UID);
      if(index !== -1){
        var uid = that.state.selected[index];
        that.state.selected[index] = that.state.selected[index + delta];
        that.state.selected[index + delta] = uid;
      }
      that.selectionUpdated();
    },

    renderSelected: function(){
      var that = this;
      var content;
      if(this.state.items.length === 0){
        content = D.p({ className: 'castle-relateditems-empty'},
                        this.props.noItemsSelectedText);
      } else {
        var items = [];
        that.state.items.forEach(function(item, idx){
          var iconClass = 'contenttype-document contenttype-' + item.portal_type.toLowerCase();
          if(item.portal_type === 'Folder'){
            iconClass = 'contenttype-folder';
          }
          var icon = D.span({className: iconClass, key: item.UID + '-icon'});

          var buttons = [
            D.button({ className: 'icon-trash plone-btn plone-btn-default',
                       onClick: that.removeClicked.bind(that, item)}, 'Remove')];
          if(idx !== 0){
            buttons.push(D.button({
              className: 'icon-move-up plone-btn plone-btn-default',
              onClick: that.move.bind(that, item, -1)}, 'Up'));
          }
          if(idx < (that.state.items.length - 1)){
            buttons.push(D.button({
              className: 'icon-move-down plone-btn plone-btn-default',
              onClick: that.move.bind(that, item, 1)}, 'Down'));
          }
          items.push(D.tr({}, [
            D.td({}, [icon, item.Title]),
            D.td({}, D.a({ href: that.props.portal_url + item.path + '/view', target: '_blank'}, item.path)),
            D.td({}, buttons)
          ]));
        });
        content = D.table({className: 'contents table'}, [
          D.thead({}, D.tr({}, [
            D.th({}, 'Title'),
            D.th({}, 'Path'),
            D.th({}, 'Actions')
          ])),
          D.tbody({}, items)
        ]);
      }
      return D.div({ className: 'castle-relateditems-selected'}, content);
    },

    render: function(){
      var buttons = [D.button({
          className: 'plone-btn plone-btn-default castle-btn-browse',
          onClick: this.browseClicked
        }, 'Browse')];
      if(this.props.allowAdd){
        buttons.push(D.button({
          className: 'plone-btn plone-btn-default castle-btn-add',
          onClick: this.addClicked
        }, 'Add'));
      }
      return D.div({className: 'castle-relateditems-container'}, [
        D.div({ className: 'castle-relateditems-selectors row'}, [
          D.div({ className: 'col-xs-12 col-md-3 castle-re-select'}, buttons),
          D.div({ className: 'col-xs-12 col-md-9 castle-re-search'}, [
            D.label({ className: 'visually-hidden', htmlFor: 'reSearch' }, 'Search'),
            D.input({ id: 'reSearch', ref: 'select2' }),
          ])
        ]),
        this.renderSelected()
      ]);
    }
  });

  var RelatedItems = Base.extend({
    browsing: true,
    name: 'relateditems',
    trigger: '.pat-relateditems',
    parser: 'mockup',
    currentPath: '/',
    defaults: {
      vocabularyUrl: null, // must be set to work
      width: '100%',
      multiple: true,
      tokenSeparators: [',', ' '],
      separator: ',',
      selectableTypes: null, // null means everything is selectable, otherwise a list of strings to match types that are selectable
      attributes: ['UID', 'Title', 'portal_type', 'path', 'getURL',
                   'getIcon','is_folderish','review_state'],
      maximumSelectionSize: -1,
      initialPath: null,
      baseCriteria: [],
      allowAdd: true,
      setupAjax: function() {
        // Setup the ajax object to use during requests
        var self = this;
        if (self.query.valid) {
          return self.query.selectAjax();
        }
        return {};
      }
    },

    init: function(){
      var that = this;

      if(that.options.initialPath){
        that.currentPath = that.options.initialPath;
      }

      var options = cutils.extend(this.options, {
        parent: this,
        input: this.$el[0],
        updateValue: function(selected){
          that.$el.attr('value', selected.join(that.options.separator));
          that.$el.trigger('change');
        }
      });
      var el = document.createElement('div');
      this.$el.parent().append(el);
      this.$el.hide();
      this.$el.parent().find('#reSearch').remove();

      // initialize value...
      var val = that.$el.attr('value');

      that.component = R.render(R.createElement(RelatedItemsComponent, options), el);
      this.$el[0].component = that.component;
      var selected;
      if(val){
        selected = val.split(that.options.separator);
      }else{
        selected = [];
      }
      that.component.setState({
        selected: selected
      });
      that.component.load();
    }
  });

  RelatedItems.Component = RelatedItemsComponent;

  return RelatedItems;

});
