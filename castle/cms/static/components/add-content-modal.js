/* global define */


define([
  'jquery',
  'castle-url/libs/react/react.min',
  'castle-url/components/modal',
  'castle-url/components/upload',
  'castle-url/components/utils',
  'mockup-utils',
  'castle-url/components/content-browser',
  'underscore'
], function($, R, Modal, Upload, cutils, utils, ContentBrowserComponent, _) {
  'use strict';

  var D = R.DOM;

  var notContentIds = [
    'plone-contentmenu-settings',
    'plone-contentmenu-more'];

  var _checkTimeout = 0;

  var AddContentTab = R.createClass({
    getInitialState: function(){
      return {
        selectedType: null,
        valid: false,
        basePath: '/',
        id: '',
        title: '',
        status: null,
        stateInfo: null,
        transitionTo: null,
        createdContent: [],
        zIndex: 3000,
        shown: false,
        preventClose: false
      };
    },

    contentTypeClicked: function(type, e){
      if(notContentIds.indexOf(type.id) !== -1){
        return;
      }
      var that = this;
      e.preventDefault();
      that.props.title = 'Add ' + type.title;
      that.setState({
        selectedType: type,
        basePath: type.folderPath || '/'
      }, function(){
        // auto focus title node after load
        $(that.refs.contentTitle.getDOMNode()).focus();
        that.props.parent.forceUpdate();
      });
    },

    createAndEditClicked: function(e){
      var that = this;
      that.createClicked(e, function(data){
        if(data.valid){
          window.location = data.edit_url;
        }
      });
    },

    createClicked: function(e, callback){
      e.preventDefault();
      var that = this;
      utils.loading.show();
      $.ajax({
        method: 'POST',
        url: $('body').attr('data-portal-url') + '/@@content-creator',
        data: $.extend({}, true, that.state, {
          action: 'create',
          _authenticator: utils.getAuthenticator()
        }),
        dataType: 'json'
      }).done(function(data){
        that.setState(data);
        if(callback && typeof(callback) === "function"){
          callback(data, that);
        }else{
          that.props.afterCreationCallback(data, that);
        }
      }).fail(function(){
        that.setState({
          status: 'Error validating with server. This should not happen. Contact support',
          valid: false
        });
      }).always(function(){
        utils.loading.hide();
      });
    },

    locationChanged: function(e){
      this.setState({
        basePath: e.target.value || '/',
        valid: false
      });
      this.check();
    },

    titleChanged: function(e){
      this.setState({
        title: e.target.value,
        id: e.target.value.replace(/ /g, '-').replace(/[^\w\s-]/gi, '').toLowerCase(),
        valid: false
      });
      this.check();
    },

    idChanged: function(e){
      this.setState({
        id: e.target.value,
        valid: false
      });
      this.check();
    },

    getFullPath: function(){
      var path = this.state.basePath;
      if(path[path.length - 1] !== '/'){
        path += '/';
      }
      return path + this.state.id;
    },

    check: function(){
      var that = this;

      clearTimeout(_checkTimeout);
      _checkTimeout = setTimeout(function(){
        if(!that.state.id || !that.state.title){
          return;
        }
        utils.loading.show();
        $.ajax({
          url: $('body').attr('data-portal-url') + '/@@content-creator',
          data: $.extend({}, true, that.state, {
            action: 'check'
          }),
          dataType: 'json'
        }).done(function(data){
          that.setState(data);
        }).fail(function(){
          that.setState({
            status: 'Error validating with server. This should not happen. Contact support',
            valid: false
          });
        }).always(function(){
          utils.loading.hide();
        });
      }, 500);
    },

    browsing: true,
    selectFolderClicked: function(e){
      e.preventDefault();
      var that = this;

      var query = new utils.QueryHelper({
        vocabularyUrl: $('body').attr('data-portal-url') + '/@@getVocabulary?name=plone.app.vocabularies.Catalog',
        batchSize: 18,
        pattern: this,
        sort_on: 'getObjPositionInParent',
        sort_order: 'ascending',
        attributes: ['UID', 'Title', 'portal_type', 'path', 'review_state', 'is_folderish'],
        baseCriteria: [{
          i: 'portal_type',
          o: 'plone.app.querystring.operation.list.contains',
          v: ['Folder']
        }]
      });
      query.currentPath = '/';

      var ContentBrowserBinder = cutils.BindComponentFactoryRoot(
          ContentBrowserComponent, function(){
            return {
              onSelectItem: function(item){
                that.setState({
                  basePath: item.path,
                  valid: false
                });
                that.check();
              },
              query: query
            };
          }, 'content-browser-react-container');
      ContentBrowserBinder({});
    },

    renderSelectionContent: function(){
      var that = this;
      var constrain = '';
      if(this.props.canConstrainTypes){
        constrain = D.div({ className: 'castle-constrain-types'}, [
          D.a({ href: this.props.constrainUrl,
                className: 'plone-btn plone-btn-default '}, 'Constrain allowed types')
        ]);
      }
      return D.div({ className: 'wrapper'}, [
        D.ul({ className: 'select-type'}, this.props.types.map(function(type){
          return D.li({ className: 'contenttype-' + type.safeId + '-container'},
            D.a({ className: 'contenttype-' + type.safeId, onClick: that.contentTypeClicked.bind(that, type)}, type.title)
          );
        })),
        constrain
      ]);
    },

    renderAddContent: function(){
      var that = this;

      var status = '';
      if(this.state.status){
        status = D.div({ className: 'portalMessage warning'}, [
          D.strong({}, 'Warning'),
          this.state.status
        ]);
      }
      var states = [D.option({}, 'Private')];
      if(this.state.stateInfo !== null){
        states = [D.option({}, this.state.stateInfo.initial.title)];
        _.each(_.keys(that.state.stateInfo.possible_states), function(state_id){
          var state = that.state.stateInfo.possible_states[state_id];
          states.push(D.option({ value: state.transition }, state.title));
        });
      }

      return D.div({ className: 'wrapper' }, [
        D.div({ className: 'input-group'}, [
          D.label({ className: 'input-group-addon', for_: 'contentTitle'}, 'Title'),
          D.input({ type: 'text', className: 'form-control', id: 'contentTitle',
                  placeholder: 'Title of content', value: this.state.title, ref: 'contentTitle',
                  onChange: this.titleChanged })
        ]),
        D.div({ className: 'input-group'}, [
          D.label({ className: 'input-group-addon', for_: 'contentId'}, 'ID'),
          D.input({ type: 'text', className: 'form-control', id: 'contentId',
                  placeholder: 'ID of the content', value: this.state.id,
                  onChange: this.idChanged })
        ]),
        D.div({ className: 'input-group'},[
          D.label({ className: 'input-group-addon'}, [
            'Folder ',
            D.a({ href: '#', className: 'contenttype-folder',
                  onClick: this.selectFolderClicked })
          ]),
          D.input({ type: 'text', className: 'form-control', id: 'contentLocation',
                  placeholder: 'Where on the site?', value: this.state.basePath,
                  onChange: this.locationChanged })
        ]),
        D.div({ className: 'input-group'}, [
          D.label({ className: 'input-group-addon' }, 'Url'),
          D.input({ type: 'text', className: 'form-control', value: this.getFullPath(), disabled: true })
        ]),
        D.div({ className: 'input-group'}, [
          D.label({ className: 'input-group-addon' }, 'State'),
          D.select({ className: 'form-control', onChange: that.stateSelected,
                     value: that.state.transitionTo, id: 'contentState',}, states)
        ]),
        status
      ]);
    },

    addAnotherClicked: function(e){
      this.setState({
        addAnother: e.target.value === 'add'
      });
    },

    stateSelected: function(e){
      this.setState({
        transitionTo: e.target.value
      });
    },

    renderHeader: function(){
      var title = 'Add';
      if(this.state.selectedType){
        title += ' ' + this.state.selectedType.title;
      }
      return [
        D.button({ type: 'button', className: 'close', 'data-dismiss': 'modal'}, [
          D.div({ className: 'close-button' }),
          D.span({ 'aria-hidden': 'true' }, '\u00d7')
        ]),
        D.h4({}, title)
      ];
    },

    render: function(){
      return D.div({ className: 'modal-content' }, [
        D.div({ className: 'modal-header' }, this.renderHeader()),
        D.div({ className: 'modal-body'}, this.renderContent()),
        D.div({ className: 'modal-footer'}, this.renderFooter())
      ]);
    },

    renderContent: function(){
      var that = this;
      var content;
      if(that.state.selectedType === null){
        content = that.renderSelectionContent();
      }else{
        content = that.renderAddContent();
      }

      return D.div({ className: 'pat-autotoc autotabs fullsize'}, [
        D.nav({ className: 'autotoc-nav'}, [
          this.props.parent.renderTabItem('add'),
          this.props.parent.renderTabItem('upload')
        ]),
        content
      ]);
    },

    renderFooter: function(){
      var buttons = [];
      if(this.state.selectedType !== null){
        buttons.push(D.button({ type: 'button', className: 'plone-btn plone-btn-default', onClick: this.goBack }, 'Cancel'));
        var disabled = false;
        if(!this.state.valid){
          disabled = true;
        }
        buttons.push(D.button({ type: 'button', className: 'plone-btn btn-default',
                                onClick: this.createClicked, disabled: disabled }, 'Create'));
        if(this.props.allowEditAfterCreation){
          buttons.push(D.button({ type: 'button', className: 'plone-btn plone-btn-primary',
                                onClick: this.createAndEditClicked, disabled: disabled }, 'Create and Edit'));
        }
      }else{
        buttons.push(D.button({ type: 'button', className: 'plone-btn plone-btn-primary', 'data-dismiss': 'modal' }, 'Done'));
      }
      var contentList = '';
      if(this.state.createdContent.length > 0){
        contentList = D.div({ className: 'content-list'}, [
          D.h4({}, 'Created content'),
          D.ul({}, this.state.createdContent.map(function(content){
            return D.li({}, [
              content.title + ' | ',
              D.a({ href: content.url, target: '_blank' }, 'View'),
              ' | ',
              D.a({ href: content.edit_url, target: '_blank' }, 'Edit')
            ]);
          })),
          D.hr({})
        ]);
      }
      return D.div({}, [
        contentList,
        D.div({className: 'btn-container'}, buttons)

      ]);
    },

    goBack: function(e){
      e.preventDefault();
      this.setState({
        valid: false,
        id: '',
        title: '',
        selectedType: null,
        status: null,
        stateInfo: null,
        transitionTo: null
      });
    },

    getDefaultProps: function(){
      return {
        types: [],
        allowEditAfterCreation: true,
        afterCreationCallback: function(data, cmp){
          cmp.state.createdContent.push(data);
          cmp.setState({
            valid: false,
            id: '',
            title: '',
            selectedType: null,
            status: null,
            stateInfo: null,
            transitionTo: null
          });
        }
      };
    },

    getModalEl: function(){
      return this.props.parent.getModalEl();
    }

  });



  var AddContentModal = cutils.Class([Modal], {
    /* tabbed */
    tabs: {
      add: {
        Component: AddContentTab,
        id: 'add-content-modal',
        title: 'Add content',
        tabLabel: 'Add'
      },
      upload: {
        Component: Upload.component,
        id: 'upload-content-modal',
        title: 'Upload',
        tabLabel: 'Upload'
      }
    },

    getDefaultProps: function(){
      return {
        update: false
      }
    },

    getId: function(){
      return this.getTab().id;
    },

    getTitle: function(){
      return this.getTab().title;
    },

    getTab: function(){
      return this.tabs[this.state.selected];
    },

    getInitialState: function(){
      var initSelected = 'add';
      if (this.props.update) {
        initSelected = 'upload'
      }
      return cutils.extend(Modal.getInitialState.apply(this), {
        selected: initSelected
      });
    },

    renderTabItem: function(tabName){
      var tab = this.tabs[tabName];
      var className = 'autotoc-level-' + tabName;
      var label = tab.tabLabel;
      if(this.state.selected === tabName){
        className += ' active';
        if(tabName === 'add' && this.refs.tab && this.refs.tab.state.selectedType){
          label = label += ' ' + this.refs.tab.state.selectedType.title;
        }
      }
      return D.a({ href: '#' + tabName, className: className,
                   onClick: this.tabClicked.bind(this, tabName)}, label);
    },

    tabClicked: function(tabName, e){
      e.preventDefault();
      this.setState({
        selected: tabName
      });
    },

    renderContentContainer: function(){
      return R.createElement(this.getTab().Component, cutils.extend(this.props, {
        ref: 'tab',
        parent: this
      }));
    }

  });

  return AddContentModal;
});
