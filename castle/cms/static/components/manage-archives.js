/* global history */
/* designed to be loaded in manage archive file,
   not included arbitrarily right now */

function getQueryVariable(variable) {
  'use strict';
   var query = window.location.search.substring(1);
   var vars = query.split('&');
   for (var i = 0; i < vars.length; i++) {
       var pair = vars[i].split('=');
       if (decodeURIComponent(pair[0]) == variable) {
           return decodeURIComponent(pair[1]);
       }
   }
}

require([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'ace'
], function($, R, utils){
  'use strict';

  var D = R.DOM;

  var HasHistory = !!window.history;
  var InitialPath = getQueryVariable('path');

  var ArchiveListing = R.createClass({
    getInitialState: function(){
      return {
        items: [],
        path: InitialPath || '/',
        selected: [],
        previousSelected: null
      };
    },

    componentDidMount: function(){
      this.load();
    },

    load: function(){
      var that = this;
      utils.loading.show();
      var url = window.location.origin + window.location.pathname;
      $.ajax({
        url: url,
        data: {
          api: 'true',
          method: 'list',
          path: that.state.path
        },
        cache: false
      }).done(function(items){
        that.setState({
          items: items,
          previousSelected: null
        });
        if(HasHistory){
          history.pushState({
            path: that.state.path
          }, "", url + '?path=' + that.state.path);
        }
      }).always(function(){
        utils.loading.hide();
      });
    },

    editClicked: function(item, e){
      e.preventDefault();
      this.props.parent.editItem(item);
    },

    deleteClicked: function(item, e){
      var that = this;
      e.preventDefault();
      if(confirm('Are you sure you want to delete this item? This can not be undone.')){
        utils.loading.show();
        $.ajax({
          url: window.location.origin + window.location.pathname,
          method: 'POST',
          data: {
            api: 'true',
            method: 'delete',
            path: item.path,
            _authenticator: utils.getAuthenticator()
          }
        }).done(function(){
          utils.loading.hide();
          that.load();
        }).fail(function(){
          utils.loading.hide();
          alert('error deleting');
        });
      }
    },

    renderItem: function(item, idx){
      var entry = D.td({}, item.id);
      var actions = [];
      if(item.is_folder){
        entry = D.td({}, D.a({ href: '#', onClick: this.setPathClicked.bind(this, item.path)}, item.id));
      }else{
        actions = [
          D.a({ href: item.url, target: '_blank' }, [
            D.span({ className: 'glyphicon glyphicon-eye-open'}),
            'View'
          ]),
          D.a({ href: '#',
                onClick: this.editClicked.bind(this, item)}, [
            D.span({ className: 'glyphicon glyphicon-pencil'}),
            'Edit'
          ]),
          D.a({ href: '#',
                onClick: this.deleteClicked.bind(this, item)}, [
            D.span({ className: 'glyphicon glyphicon-trash'}),
            'Delete'
          ])
        ];
      }
      return D.tr({key: item.path}, [
        D.td({}, D.input({ type: 'checkbox',
                           checked: this.state.selected.indexOf(item.path) !== -1,
                           onClick: this.selectItem.bind(this, item, idx)})),
        entry,
        D.td({}, actions)
      ]);
    },

    selectItem: function(item, idx, e){
      var selected = this.state.selected;
      var items = this.state.items;
      var index = selected.indexOf(item.path);
      if(e.shiftKey && this.state.previousSelected !== null){
        // held shift key while doing this, see if we can select a group
        var start = this.state.previousSelected;
        var end = idx;
        if(start > end){
          end = start;
          start = idx;
        }
        items.slice(start, end + 1).forEach(function(item){
          selected.push(item.path);
        });
      }else if(index === -1){
        // add
        this.state.selected.push(item.path);
      }else{
        // remove
        selected.splice(index, 1);
      }
      this.setState({
        selected: selected,
        previousSelected: idx
      });
    },

    setPathClicked: function(path, e){
      e.preventDefault();
      this.state.path = path;
      this.load();
    },

    clearSelectedClicked: function(e){
      e.preventDefault();
      this.setState({
        selected: []
      });
    },

    deleteSelectedClicked: function(e){
      var that = this;
      e.preventDefault();
      if(confirm('Are you sure you want to delete the selected items? This can not be undone.')){
        utils.loading.show();
        $.ajax({
          url: window.location.origin + window.location.pathname,
          method: 'POST',
          data: {
            api: 'true',
            method: 'deletegroup',
            paths: JSON.stringify(that.state.selected),
            _authenticator: utils.getAuthenticator()
          }
        }).done(function(){
          utils.loading.hide();
          that.state.selected = [];
          that.load();
        }).fail(function(){
          utils.loading.hide();
          alert('error deleting');
        });
      }
    },

    renderBreadcrumbs: function(){
      var that = this;
      var parts = '/';
      if(that.state.path !== '/'){
        parts = [
          '/',
          D.a({ href: '#', onClick: that.setPathClicked.bind(that, '/') }, 'Home'),
          '/'
        ];

        var trail = '/';
        that.state.path.split('/').forEach(function(part){
          if(part === '/' || !part){
            return;
          }
          if(trail !== '/'){
            trail += '/';
          }
          trail += part;
          parts.push(D.a({ href: '#', onClick: that.setPathClicked.bind(that, trail)}, part));
          parts.push('/');
        });
      }
      return D.div({}, [
        parts,
        D.span({ className: 'pull-right'}, that.state.items.length + ' items in folder')
      ]);
    },

    allSelected: function(){
      for(var i=0; i<this.state.items.length; i++){
        if(this.state.selected.indexOf(this.state.items[i].path) === -1){
          return false;
        }
      }
      return true;
    },

    selectAllClicked: function(){
      var off = this.allSelected();
      var selected = this.state.selected;
      for(var i=0; i<this.state.items.length; i++){
        var item = this.state.items[i];
        if(off){
          var index = selected.indexOf(item.path);
          if(index !== -1){
            selected.splice(index, 1);
          }
        }else{
          if(selected.indexOf(item.path) === -1){
            selected.push(item.path);
          }
        }
      }
      this.setState({
        selected: selected
      });
    },

    renderTable: function(){
      var that = this;
      var items = [];
      that.state.items.forEach(function(item, idx){
        items.push(that.renderItem(item, idx));
      });
      return D.table({ className: 'table table-striped'}, [
        D.thead({}, [
          D.tr({}, D.td({ colSpan: 3 }, that.renderBreadcrumbs())),
          D.tr({}, [
            D.th({}, D.input({ type: 'checkbox', onClick: this.selectAllClicked,
                               checked: this.allSelected()})),
            D.th({}, 'Name'),
            D.th({}, 'Actions')
          ])
        ]),
        D.tbody({}, items)
      ]);
    },

    renderButtons: function(){
      var that = this;
      var deleteTxt = 'Delete';
      if(that.state.selected.length > 0){
        deleteTxt += ' (' + that.state.selected.length + ')';
      }
      return D.div({ className: 'btn-container' }, [
        D.button({ className: 'plone-btn plone-btn-danger',
                   disabled: that.state.selected.length === 0,
                   onClick: this.deleteSelectedClicked }, deleteTxt),
        D.button({ className: 'plone-btn plone-btn-default',
                   disabled: that.state.selected.length === 0,
                   onClick: that.clearSelectedClicked }, 'Clear selected'),
      ]);
    },

    renderSelected: function(){
      if(this.state.selected.length === 0){
        return '';
      }
      return D.div({}, [
        D.strong({}, 'Selected:'),
        D.span({}, this.state.selected.join(', '))
      ]);
    },

    render: function(){
      var that = this;
      return D.div({}, [
        that.renderButtons(),
        that.renderTable(),
        that.renderSelected()
      ]);
    }
  });

  var ArchiveEdit = R.createClass({
    getInitialState: function(){
      return {
        item: null,
        loadedPath: null,
        value: ''
      };
    },
    componentDidMount: function(){
      this.load();
    },

    componentDidUpdate: function(){
      this.load();
    },

    load: function(){
      var that = this;
      if(!that.state.item || that.state.item.path === this.state.loadedPath){
        return;
      }

      utils.loading.show();
      $.ajax({
        url: window.location.origin + window.location.pathname,
        data: {
          api: 'true',
          method: 'get',
          path: that.state.item.path
        },
        cache: false
      }).done(function(data){
        that.setState({
          loadedPath: that.state.item.path,
          value: data.data
        });
        utils.loading.hide();
      }).fail(function(){
        utils.loading.hide();
      });
    },

    saveClicked: function(e){
      var that = this;
      e.preventDefault();
      utils.loading.show();
      $.ajax({
        url: window.location.origin + window.location.pathname,
        data: {
          api: 'true',
          method: 'save',
          path: that.state.item.path,
          value: that.state.value,
          _authenticator: utils.getAuthenticator()
        },
        method: 'POST'
      }).done(function(){
        utils.loading.hide();
        that.cancelClicked();
      }).fail(function(){
        utils.loading.hide();
        alert('error saving');
      });
    },

    cancelClicked: function(e){
      if(e){
        e.preventDefault();
      }
      this.setState({
        item: null,
        loadedPath: null,
        value: ''
      });
      this.props.parent.setState({
        view: 'list',
        data: {}
      });
    },

    valueChanged: function(e){
      this.setState({
        value: e.target.value
      });
    },

    render: function(){
      var label = 'Edit ';
      if(this.state.item){
        label += this.state.item.path;
      }
      return D.div({}, [
        D.h4({}, label),
        D.textarea({ value: this.state.value, onChange: this.valueChanged,
                     style: { height: '600px' }}),
        D.div({ className: 'btn-container' }, [
          D.button({ className: 'plone-btn plone-btn-primary',
                     onClick: this.saveClicked }, 'Save'),
          D.button({ className: 'plone-btn plone-btn-default',
                     onClick: this.cancelClicked }, 'Cancel'),
        ])
      ]);
    }
  });

  var ArchiveManager = R.createClass({
    getInitialState: function(){
      return {
        view: 'list',
        data: {}
      };
    },

    editItem: function(item){
      this.refs.editor.setState({
        item: item
      });
      this.setState({
        view: 'edit'
      });
    },

    componentDidMount: function(){

    },

    render: function(){
      return D.div({}, [
        D.div({ style: this.state.view !== 'list' && {display: 'none'} || {},
                className: 'castle-archival-browser-container'},
          R.createElement(ArchiveListing, { parent: this, ref: 'listing'})),
        D.div({ style: this.state.view !== 'edit' && {display: 'none'} || {},
                className: 'castle-archival-edit'},
          R.createElement(ArchiveEdit, { parent: this, ref: 'editor'}))
      ]);
    }
  });

  var el = document.getElementById('archives-container');
  var component = R.render(R.createElement(ArchiveManager, {}), el);

  window.onpopstate = function(e){
    if(e.state){
      component.refs.listing.state.path = e.state.path;
      component.refs.listing.load();
    }
  };

  if(HasHistory){
    if(InitialPath){
      history.replaceState({
        path: InitialPath
      }, "", window.location.origin + window.location.pathname + '?path=' + InitialPath);
    }else{
      history.replaceState({
        path: '/'
      }, "", window.location.origin + window.location.pathname + '?path=/');
    }
  }
});
