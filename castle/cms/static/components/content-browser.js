/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/modal',
  'castle-url/components/utils',
  'mockup-ui-url/views/popover',
  'mockup-patterns-querystring'
], function($, Base, _, R, utils, Modal, cutils,
            PopoverView, QueryString) {
  'use strict';
  var D = R.DOM;


  var TableListingView = R.createClass({

    allSelected: function(){
      var that = this;
      var items = that.props.parent.state.items;
      var selected = this.getAllSelected();
      for(var i=0; i<items.length; i++){
        var item = items[i];
        if(selected.indexOf(item.UID) === -1){
          return false;
        }
      }
      return true;
    },

    getAllSelected: function(){
      var that = this;
      var selected = [];
      that.props.parent.state.selected.forEach(function(item){
        selected.push(item.UID);
      });
      return selected;
    },

    selectAllClicked: function(e){
      var that = this;
      var items = that.props.parent.state.items;
      var selected = this.getAllSelected();
      for(var i=0; i<items.length; i++){
        var item = items[i];
        if(selected.indexOf(item.UID) === -1){
          that.props.onItemSelected.bind(that.props.parent, item)(e);
        }
      }
    },

    render: function(){
      var that = this;
      var props = that.props;
      var parent = props.parent;
      var items = parent.state.items;

      var selectAllCheckbox = '';
      if(parent.props.multiple){
        selectAllCheckbox = D.input({ type: 'checkbox', checked: that.allSelected(),
                                      onClick: that.selectAllClicked });
      }

      return D.table({className: 'contents table'}, [
        D.thead({}, D.tr({}, [
          D.th({}, selectAllCheckbox),
          D.th({}, 'Title'),
          D.th({}, 'Type'),
          D.th({}, 'State')
        ])),
        D.tbody({}, items.map(function(item){
          var iconClass = 'contenttype-document contenttype-' + item.portal_type.toLowerCase();
          if(item.portal_type === 'Folder'){
            iconClass = 'contenttype-folder';
          }
          var icon = D.span({className: iconClass, key: item.UID + '-icon'});

          var selected = false;
          _.each(parent.state.selected, function(existingItem){
            if(existingItem.UID === item.UID){
              selected = true;
            }
          });
          var className = '';
          var onClick = props.onItemSelected.bind(parent, item);
          var clickText = 'Select';
          if(selected){
            className += ' active';
            clickText = 'Remove';
            onClick = props.onItemRemoved.bind(parent, item);
          }
          var title = [icon, D.span({ className: 'content-title'}, item.Title)];
          if(item.is_folderish){
            title = D.a({className: 'folderBox', href: '#2',
                         onClick: props.onFolderSelected.bind(parent, item)},
                        title);
          }
          className += 'state-' + item.review_state;
          var checkbox = '';
          if(parent.props.selectableTypes === null ||
              parent.props.selectableTypes.indexOf(item.portal_type) !== -1){
            checkbox = D.input({type: 'checkbox', checked: selected, onClick: onClick});
          }
          return D.tr({ key: item.UID, className: className }, [
            D.td({}, checkbox),
            D.td({}, title),
            D.td({}, item.portal_type),
            D.td({}, item.review_state)
          ]);
        }))
      ]);
    },
    getDefaultProps: function(){
      return {
        parent: null,
        onItemSelected: function(){},
        onItemRemoved: function(){},
        onFolderSelected: function(){}
      };
    }
  });

  var ImageListingView = R.createClass({
    render: function(){
      var that = this;
      var props = that.props;
      var parent = props.parent;
      var items = parent.state.items;

      // hasImage
      var placeHolderUrl = $('body').attr('data-portal-url') + '/++plone++castle/images/placeholder-image.png';
      var folderPlaceholderUrl = $('body').attr('data-portal-url') + '/++plone++castle/images/placeholder-folder.png';
      return D.div({className: 'row images-container'}, items.map(function(item){
        var imgUrl = placeHolderUrl;
        if(item.hasImage){
          imgUrl = item.getURL + '/@@images/image/preview';
        }
        if(!item.hasImage && item.is_folderish){
          imgUrl = folderPlaceholderUrl;
        }
        var img = D.div({ className: 'image-responsive', style: {'background-image': 'url("' + imgUrl + '")' }});
        if(item.is_folderish){
          img = D.a({ href: '#', onClick: props.onFolderSelected.bind(parent, item)}, img);
        }else{
          img = D.a({ href: '#', onClick: props.onItemSelected.bind(parent, item)}, img);
        }

        var selected = false;
        parent.state.selected.forEach(function(existingItem){
          if(existingItem.UID === item.UID){
            selected = true;
          }
        });

        return D.div({ className: 'col-md-3 image-item', key: item.UID}, D.div({ className: 'image-wrapper'}, [
          img,
          D.p({ className: 'image-title'}, [
            D.label({ htmlFor: item.UID + '-imageselect'},[
              D.input({type: 'checkbox', checked: selected,
                       onClick: props.onItemSelected.bind(parent, item),
                       id: item.UID + '-imageselect' }),
              item.Title
            ])
          ]),
        ]));
      }));
    }
  });

  var ContentBrowserComponent = cutils.Class([Modal], {
    getInitialState: function(){
      return {
        error: false,
        items: [],
        page: 1,
        total: 0,
        filter: '',
        selected: [],
        sort_on: 'modified',
        sort_order: 'reverse',
        view: 'table',
        showQuery: false,
        criterias: [],
      };
    },
    componentDidMount: function(){
      var that = this;
      Modal.componentDidMount.apply(this);

      // default to current path..
      var basePath = $('body').attr('data-base-path');
      if((that.props.query.currentPath === '/' || that.props.query.pattern.currentPath === '/') &&
          basePath){
        that.setPath(basePath);
      }

      that.load();

      var btnEl = that.refs.query_btn.getDOMNode();
      var $btnEl = $(btnEl);
      var el = that.refs.query_popover.getDOMNode();
      var $el = $(el);

      that.props.query_popover = new PopoverView({
        id: 'content-browser-query',
        title: 'Query',
        useBackdrop: false,
        content: _.template('<input class="pat-querystring" />'),
        placement: 'left'
      });
      that.props.query_popover.getPosition = function() {
        return $.extend({}, {
          width: btnEl.offsetWidth,
          height: btnEl.offsetHeight
        }, $btnEl.offset());
      };
      $el.append(that.props.query_popover.render().el);
      that.props.query_popover.$el.addClass('query');
      var $queryString = that.props.query_popover.$('input.pat-querystring');
      var queryString = new QueryString(
        $queryString, {
          indexOptionsUrl: $('body').attr('data-portal-url') + '/@@qsOptions',
          showPreviews: false
        }
      );

      queryString.$el.on('change', function() {
        if (that._qsTimeout) {
          clearTimeout(that._qsTimeout);
        }
        that._qsTimeout = setTimeout(function() {
          var criterias = $.parseJSON($queryString.val());
          that.setStateReload({
            criterias: criterias,
            page: 1
          });
        }, 200);
      });
      queryString.$el.on('initialized', function() {
        queryString.$sortOn.on('change', function() {
          that.setStateReload({
            sort_on: queryString.$sortOn.val(),
            page: 1
          });
        });
        queryString.$sortOrder.change(function() {
          var order = 'ascending';
          if (queryString.$sortOrder[0].checked) {
            order = 'reverse'; // jshint ignore:line
          }
          that.setStateReload({
            sort_order: order,
            page: 1
          });
        });

        queryString.component.props.storage.dispatcher.handleViewAction({
          actionType: 'update',
          data: {
            sortOn: that.state.sort_on,
            reversed: that.state.sort_order === 'reverse'
          }
        });
        queryString.component.setState({
          sortOn: that.state.sort_on,
          reversed: that.state.sort_order === 'reverse'
        });
      });
    },

    load: function(){
      var that = this;
      utils.loading.show();
      $.ajax({
        url: that.getQueryUrl(),
        dataType: 'json'
      }).done(function(data){
        that.setState({
          items: data.results,
          total: data.total
        });
      }).fail(function(){
        that.setState({
          error: true,
          items: [],
          total: 0
        });
      }).always(function(){
        utils.loading.hide();
      });
    },
    getQueryUrl: function(){
      var that = this;
      var query = that.props.query;

      if(query.options.attributes.indexOf('getURL') === -1){
        query.options.attributes.push('getURL');
      }
      if(query.options.attributes.indexOf('hasImage') === -1){
        query.options.attributes.push('hasImage');
      }
      if(query.options.attributes.indexOf('is_folderish') === -1){
        query.options.attributes.push('is_folderish');
      }

      query.options.sort_on = this.state.sort_on;
      query.options.sort_order = this.state.sort_order;
      query.options.useBaseCriteria = true;
      var baseCriteria = this.props.baseCriteria.slice();
      query.options.baseCriteria = baseCriteria.concat(that.state.criterias.slice());
      if(that.state.filter){
        query.options.baseCriteria.push({
          i: 'Title',
          o: 'plone.app.querystring.operation.string.contains',
          v: that.state.filter
        });
      }
      if(!query.options.sort_on){
        query.options.sort_on = 'getObjPositionInParent';
      }

      var params = query.getQueryData();
      params.batch = JSON.stringify(query.getBatch(that.state.page));

      var url = query.options.vocabularyUrl;
      if (url.indexOf('?') === -1) {
        url += '?';
      } else {
        url += '&';
      }
      return url + $.param(params);
    },

    itemSelected: function(item, e){
      var that = this;
      if(e.target.nodeName !== 'INPUT'){
        e.preventDefault();
      }
      if(that.props.multiple){
        var selected = that.state.selected;
        var found = false;
        that.state.selected.forEach(function(existing){
          if(existing.UID === item.UID){
            found = true;
          }
        });
        if(found){
          this.removeSelected(item);

        }else{
          selected.push(item);
          that.setState({
            selected: selected
          });
        }
      }else{
        that.props.onSelectItem(item);
        that.hide();
      }
    },

    removeSelected: function(item){
      var newSelected = [];
      _.each(this.state.selected, function(existingItem){
        if(existingItem.UID !== item.UID){
          newSelected.push(existingItem);
        }
      });
      this.setState({
        selected: newSelected
      });
    },

    folderSelected: function(item, e){
      e.preventDefault();
      var that = this;
      that.setPath(item.path);
      that.state.filter = '';
      that.state.page = 1;
      that.load();
    },

    setPath: function(path){
      var that = this;
      that.props.query.currentPath = path;
      if(that.props.query.pattern){
        that.props.query.pattern.currentPath = path;
      }
    },

    renderItems: function(){
      if(this.state.view === 'table'){
        return R.createElement(TableListingView, {
          parent: this,
          onItemSelected: this.itemSelected,
          onItemRemoved: this.removeSelected,
          onFolderSelected: this.folderSelected
        });
      }else if(this.state.view === 'image'){
        return R.createElement(ImageListingView, {
          parent: this,
          onItemSelected: this.itemSelected,
          onItemRemoved: this.removeSelected,
          onFolderSelected: this.folderSelected
        });
      }
      return [];
    },

    crumbClicked: function(path, e){
      e.preventDefault();
      this.setPath(path);
      this.state.filter = '';
      this.state.page = 1;
      this.load();
    },

    renderBreadcrumbs: function(){
      var that = this;
      var paths = that.props.query.getCurrentPath().split('/');
      paths[0] = '/';
      var itemPath = '';
      var crumbs = [];
      _.each(paths, function(node, idx) {
        if (node !== '') {
          var name = node;
          var path = '/';
          if(node === '/'){
            name = 'Home';
          }else{
            itemPath = itemPath + '/' + node;
            path = itemPath;
          }
          if(idx < paths.length - 1){
            crumbs.push(D.li({},
              D.a({ href: '#', onClick: that.crumbClicked.bind(that, path)}, name)));
          }else{
            crumbs.push(D.li({}, name));
          }
        }
      });
      return D.ol({ className: 'breadcrumb' }, crumbs);
    },

    filterChanged: function(e){
      var that = this;

      that.setStateReload({
        filter: e.target.value,
        page: 1
      });
    },

    setStateReload: function(state){
      var that = this;
      that.setState(state, function(){
        if(that._timeout){
          clearTimeout(that._timeout);
        }
        that._timeout = setTimeout(that.load, 300);
      });
    },

    queryClicked: function(e){
      var that = this;
      e.preventDefault();
      this.setState({
        showQuery: !this.state.showQuery
      }, function(){
        that.props.query_popover.toggle();
      });
    },

    renderFilter: function(){
      var queryStyle = {display: 'block'};
      if(!this.state.showQuery){
        queryStyle.display = 'none';
      }
      var className = 'castle-filter-container';
      if(this.state.criterias.length > 0 || this.state.filter.length > 0){
        className += ' active-filter';
      }
      return D.div({ className: className}, [
        D.div({className: 'input-group input-group-sm filter-group'}, [
          D.input({ type: 'text', className: 'form-control', placeholder: 'Filter',
                    onChange: this.filterChanged, value: this.state.filter}),
          D.span({ className: "input-group-btn" }, [
            D.a({ href: "#", className: "btn btn-default", id: 'castle-query-filter',
                  ref: 'query_btn', onClick: this.queryClicked }, [
              D.span({ className: "glyphicon glyphicon-search"}),
              'Query'
            ])
          ])
        ]),
        D.div({ className: 'castle-content-browser-filter-popover',
                ref: 'query_popover', style: queryStyle})
      ]);
    },

    renderContent: function(){
      var that = this;
      return D.div({ className: 'castle-content-browser'}, [
        D.div({ className: 'row top'}, [
          D.div({ className: 'col-md-5 castle-breadcrumbs-container'}, that.renderBreadcrumbs()),
          D.div({ className: 'listing-type-selector col-md-3 col-md-offset-1'}, that.renderViewSelection()),
          D.div({ className: 'col-md-3'}, that.renderFilter()),
        ]),
        that.renderItems(),
        that.renderPaging()
      ]);
    },
    pageClicked: function(page, e){
      e.preventDefault();
      this.state.page = page;
      this.load();
    },

    changeView: function(view, e){
      e.preventDefault();
      this.setState({
        view: view
      });
    },

    renderViewSelection: function(){
      return [
        D.span({ className: 'label'}, 'View as:'),
        D.button({ className: 'plone-btn plone-btn-default',
                   disabled: this.state.view === 'table',
                   onClick: this.changeView.bind(this, 'table')}, D.span({
          className: 'glyphicon glyphicon-list'
        })),
        D.button({ className: 'plone-btn plone-btn-default',
                   disabled: this.state.view === 'image',
                   onClick: this.changeView.bind(this, 'image')}, D.span({
          className: 'glyphicon glyphicon-th-large'
        }))
      ];
    },

    renderPaging: function(){
      var that = this;
      if(that.state.total <= that.props.query.options.batchSize){
        return '';
      }
      var pages = Math.ceil(that.state.total / that.props.query.options.batchSize);
      return D.div({ className: 'pagination-centered'},
        D.ul({ className: 'castle-pagination pagination-sm pagination-centered'},
          _.range(pages).map(function(page){
            var className = '';
            page += 1;
            if(page === that.state.page){
              className = 'current';
            }
            return D.li({ key: 'page' + page, className: className},
              D.a({ href: '#', onClick: that.pageClicked.bind(that, page)}, page));
          })
        )
      );
    },
    doneClicked: function(e){
      e.preventDefault();
      this.props.onSelectItems(this.state.selected);
      this.hide();
    },

    renderFooter: function(){
      var buttons = [D.button({ type: 'button', className: 'btn btn-default btn-danger',
                                onClick: this.hide }, 'Done')];
      if(this.props.multiple){
        buttons.push(D.button({
          type: 'button', className: 'btn btn-default btn-primary',
          onClick: this.doneClicked},
          'Select (' + this.state.selected.length + ')'));
      }
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'content-browser-modal',
        title: 'Select content',
        multiple: false,
        selectableTypes: null,
        onSelectItem: function(){},
        onSelectItems: function(){},
        baseCriteria: []
      });
    }
  });

  return ContentBrowserComponent;
});
