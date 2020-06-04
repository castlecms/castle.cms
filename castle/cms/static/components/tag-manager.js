require([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/utils',
  'castle-url/components/modal'
], function($, R, utils, cutils, Modal){
  'use strict';

  var D = R.DOM;

  var RenameModalComponent = cutils.Class([Modal], {
    getInitialState: function(){
      return {
        total: this.props.tag.count,
        confirmed: false,
        new_tag: ''
      };
    },

    handle: function(){
      utils.loading.show();
      var that = this;
      $.ajax({
        url: $('body').attr('data-portal-url') + '/@@tags-controlpanel',
        data: {
          action: 'rename',
          tag: that.props.tag.name,
          new_tag: that.state.new_tag,
          _authenticator: utils.getAuthenticator()
        }
      }).done(function(data){
        if(data.total === 0){
          utils.loading.hide();
          that.props.parent.load();
          that.hide();
          return;
        }
        that.setState({
          total: data.total
        }, function(){
          setTimeout(function(){
            that.handle();
          }, 1000);
        });
      }).fail(function(){
        alert('error renaming tag');
      });
    },

    newTagChanged: function(e){
      this.setState({
        new_tag: e.target.value
      });
    },

    renderRenameInput: function(){

      return D.div({}, [
        D.p({}, 'Renaming tag: ' + this.props.tag.name),
        D.div({ className: 'form-group'}, [
          D.label({}, 'New tag name'),
          D.input({ value: this.state.new_tag, onChange: this.newTagChanged, type: 'text',
                    className: 'form-control'})
        ])
      ]);
    },

    renderContent: function(){
      var content;
      if(this.state.confirmed){
        content = D.p({}, this.state.total + ' items left to rename "' + this.props.tag.name + '" to "' + this.state.new_tag + '"');
      }else{
        content = this.renderRenameInput();
      }
      return D.div({ className: 'castle-remove-tag'}, [
        content
      ]);
    },
    renderFooter: function(){
      var that = this;
      var buttons = [];
      if(!this.state.confirmed){
        buttons.push(D.button({ className: 'plone-btn plone-btn-default',
                                onClick: this.hide }, 'Cancel'));
        buttons.push(D.button({ className: 'plone-btn plone-btn-danger',
                                onClick: function(e){
                                  e.preventDefault();
                                  that.setState({
                                    confirmed: true
                                  }, function(){
                                    that.handle();
                                  });
                                }}, 'Rename tag'));
      }
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'preview-content-modal',
        title: 'Rename tag',
        tag: null
      });
    }
  });


  var RemoveModalComponent = cutils.Class([Modal], {
    getInitialState: function(){
      return {
        total: this.props.tag.count,
        confirmed: false
      };
    },

    handle: function(){
      utils.loading.show();
      var that = this;
      $.ajax({
        url: $('body').attr('data-portal-url') + '/@@tags-controlpanel',
        data: {
          action: 'remove',
          tag: that.props.tag.name,
          _authenticator: utils.getAuthenticator()
        }
      }).done(function(data){
        if(data.total === 0){
          utils.loading.hide();
          that.props.parent.load();
          that.hide();
          return;
        }
        that.setState({
          total: data.total
        }, function(){
          setTimeout(function(){
            that.handle();
          }, 1000);
        });
      }).fail(function(){
        alert('error removing tag');
      });
    },

    renderContent: function(){
      var content;
      if(this.state.confirmed){
        content = D.p({}, this.state.total + ' items left to remove tag "' + this.props.tag.name + '"');
      }else{
        content = D.p({}, 'Are you certain you want to remove the tag "' + this.props.tag.name + '"?');
      }
      return D.div({ className: 'castle-remove-tag'}, [
        content
      ]);
    },
    renderFooter: function(){
      var that = this;
      var buttons = [];
      if(!this.state.confirmed){
        buttons.push(D.button({ className: 'plone-btn plone-btn-default',
                                onClick: this.hide }, 'Cancel'));
        buttons.push(D.button({ className: 'plone-btn plone-btn-danger',
                                onClick: function(e){
                                  e.preventDefault();
                                  that.setState({
                                    confirmed: true
                                  }, function(){
                                    that.handle();
                                  });
                                }}, 'Yes, remove'));
      }
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'preview-content-modal',
        title: 'Remove tag',
        tag: null
      });
    }
  });


  var TagManagerComponent = R.createClass({
    getInitialState: function(){
      return {
        tags: [],
        page: 1,
        batch_size: 5,
        total: 0
      };
    },
    getDefaultProps: function(){
      return {};
    },

    componentDidMount: function(){
      this.load();
    },

    load: function(){
      var that = this;
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-portal-url') + '/@@tags-controlpanel',
        data: {
          action: 'get',
          page: this.state.page
        }
      }).done(function(data){
        that.setState({
          tags: data.tags,
          total: data.total,
          batch_size: data.batch_size
        });
      }).fail(function(){
        alert('error getting data');
      }).always(function(){
        utils.loading.hide();
      });
    },

    onRemoveClicked: function(tag, e){
      e.preventDefault();
      cutils.createModalComponent(RemoveModalComponent, 'castle-tag-remove-modal', {
        tag: tag,
        parent: this
      });
    },
    onRenameClicked: function(tag, e){
      e.preventDefault();
      cutils.createModalComponent(RenameModalComponent, 'castle-tag-rename-modal', {
        tag: tag,
        parent: this
      });
    },

    pageClicked: function(page, e){
      var that = this;
      e.preventDefault();
      this.setState({
        page: page
      }, function(){
        that.load();
      });
    },

    renderPagination: function(){
      var totalPages = Math.ceil(this.state.total / this.state.batch_size);
      var items = [];
      for(var i=0; i<totalPages; i++){
        var page = i + 1;
        items.push(D.li({ className: page == this.state.page && "disabled" },
          D.a({href: "#", onClick: this.pageClicked.bind(this, page)}, page)));
      }
      return D.nav({}, [
        D.ul({ className: "castle-pagination" }, items)
      ]);
    },

    renderTable: function(){
      var that = this;
      return D.table({ className: 'table'}, [
        D.thead({}, D.tr({}, [
          D.th({}, 'Tag'),
          D.th({}, 'Count'),
          D.th({}, 'Actions')
        ])),
        D.tbody({}, this.state.tags.map(function(tag){
          return D.tr({}, [
            D.td({}, tag.name),
            D.td({}, tag.count),
            D.td({}, [
              D.button({ className: 'plone-btn plone-btn-danger',
                         onClick: that.onRemoveClicked.bind(that, tag) }, 'Remove'),
              D.button({ className: 'plone-btn plone-btn-default',
                         onClick: that.onRenameClicked.bind(that, tag)}, 'Rename'),
            ]),
          ]);
        }))
      ]);
    },

    render: function(){
      return D.div({ className: 'tag-manager'}, [
        D.p({}, this.state.total + ' total tags'),
        this.renderTable(),
        this.renderPagination()
      ]);
    }
  });

  var el = document.getElementById('tag-manager');

  var component = R.render(R.createElement(TagManagerComponent, {}), el);
});
