/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/modal',
  'castle-url/components/utils',
  'mockup-patterns-modal',
  'pat-registry',
  'moment',
  'jquery.cookie'
], function($, Base, _, R, utils, Modal, cutils, ModalPattern, Registry, moment) {
  'use strict';
  var D = R.DOM;

  var SlotManagerComponent = R.createClass({
    getInitialState: function(){

      var url = $('body').attr('data-base-url').replace($('body').attr('data-portal-url'), '');
      if(!url || url[0] !== '/'){
        url = '/' + url;
      }
      return {
        current: url,
        mode: 'parent',
        effective_tiles: [],
        tiles: [],
        dirty: false
      };
    },

    componentDidMount: function(){
      var that = this;
      if(!that.props.slot.workingId){
        that.startEditing();
      }else{
        that.doAction({});
      }
    },

    startEditing: function(override){
      var that = this;
      var data = {
        action: 'copymeta',
        metaId: that.props.slot.id,
        _authenticator: utils.getAuthenticator()
      };
      if(override){
        data.override = 'yes';
      }
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-portal-url') + that.state.current + '/@@meta-tile-manager',
        data: data
      }).done(function(data){
        if(data.success){
          that.props.slot.workingId = data.newId;
          that.doAction({});
        }else if(data.locked){
          var info = data.lock_data;
          if(confirm('This slot currently has an unfinished edit started by ' + info.user +
                     ' ' + moment(info.when).fromNow() + '. Do you want to override this ' +
                     "person's edit? This will destroy of the other user's changes.")){
            that.startEditing(true);
          }
        }else{
          alert('unknown error occurred');
        }
      }).always(function(){
        utils.loading.hide();
      });
    },

    doAction: function(data, success){
      var that = this;
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-portal-url') + that.state.current + '/@@meta-tile-manager',
        data: $.extend({}, true, {
          metaId: that.props.slot.id,
          _authenticator: utils.getAuthenticator()
        }, data)
      }).done(function(data){
        data.loading = false;
        that.setState(data);
        if(success){
          success(data);
        }
      }).always(function(){
        utils.loading.hide();
      });
    },

    _editTile: function(tile){
      utils.loading.show();
      // Get url
      var tile_edit_url = this.state.current_url + '/@@edit-tile/' +
                          tile.type + '/' + tile.id + '?X-Tile-Persistent=yes';

      var modal = new ModalPattern($(this.getDOMNode()), {
        ajaxUrl: tile_edit_url,
        loadLinksWithinModal: true,
        buttons: '.formControls > input[type="submit"], .actionButtons > input[type="submit"]'
      });

      modal.$el.off('after-render');
      var $html = null;
      var tinymce = null;
      utils.loading.show();
      modal.on('after-render', function() {
        modal.$modal.parents('.plone-modal-wrapper').css('z-index', '9998');
        $('input[name*="cancel"]', modal.$modal).off('click').on('click', function() {
            // Close overlay
            modal.hide();
        });
        /* make sure it is saved persistently */
        $('form', modal.$modal).append($('<input type="hidden" name="X-Tile-Persistent" value="yes" />'));

        // setup tile mce for raw html tile
        $html = $('[name="plone.app.standardtiles.rawhtml.content"]', modal.$modal);
        if($html.size() > 0){
          var options = $.parseJSON($('body').attr('data-pat-tinymce'));
          if(options.tiny.external_plugins){
            _.each(_.keys(options.tiny.external_plugins), function(plugin){
              options.tiny.external_plugins[plugin] = $('body').attr('data-portal-url') +
                '/' +options.tiny.external_plugins[plugin];
            });
          }
          tinymce = new Registry.patterns.tinymce($html, options);
        }
        utils.loading.hide();
      });
      modal.show();
      modal.$el.off('formActionSuccess');
      modal.on('hide', function(){
        if($html){
          try{
            $html.data("pattern-tinymce").destroy();
          }catch(e){
            //
          }
          $html.removeData("pattern-tinymce");
        }
        if(tinymce && tinymce.tiny){
          tinymce.tiny.remove();
        }
      });
      modal.on('formActionSuccess', function () {
        //var tileUrl = xhr.getResponseHeader('X-Tile-Url');
        modal.hide();
      });
    },

    addTileSelected: function(e){
      var that = this;
      that.state.dirty = true;
      that.doAction({
        type: e.target.value,
        action: 'addtile'
      }, function(data){
        // XXX after it is added, go into edit mode for it immediately
        that._editTile(data.tiles[data.tiles.length - 1]);
      });
    },

    deleteTile: function(idx, e){
      var that = this;
      that.state.dirty = true;
      e.preventDefault();
      that.doAction({
        type: e.target.value,
        action: 'deletetile',
        idx: idx
      });
    },

    moveUp: function(idx, e){
      var that = this;
      that.state.dirty = true;
      e.preventDefault();
      that.doAction({
        type: e.target.value,
        action: 'moveup',
        idx: idx
      });
    },

    moveDown: function(idx, e){
      var that = this;
      that.state.dirty = true;
      e.preventDefault();
      that.doAction({
        type: e.target.value,
        action: 'movedown',
        idx: idx
      });
    },

    modeClicked: function(e){
      var that = this;
      that.state.dirty = true;
      e.preventDefault();
      that.doAction({
        value: e.target.value,
        action: 'mode'
      });
    },

    editTile: function(idx, e){
      e.preventDefault();
      this.state.dirty = true;
      this._editTile(this.state.tiles[idx]);
    },

    renderLinkedPath: function(path){
      if(path === '/'){
        return D.a({ href: $('body').attr('data-portal-url'), target: '_blank',
                     className: 'slot-manager-link-path'}, [
          D.span({ className: 'glyphicon glyphicon-home'}),
          ' /'
        ]);
      }else{
        return D.a({ href: $('body').attr('data-portal-url') + path + '/view',
                     target: '_blank', className: 'slot-manager-link-path'}, path);
      }
    },

    renderTileListing: function(){
      var that = this;
      if(this.state.mode === 'hide'){
        return D.p({ className: 'discreet'}, 'This slot is hidden');
      }

      var content = [];
      if(this.state.mode === 'parent' || this.state.mode === 'add'){
        var showParents = [];
        that.state.effective_tiles.forEach(function(effective_tile){
          if(effective_tile.path === that.state.current ||
             effective_tile.data.length === 0){
            return;
          }
          showParents.push(D.table({className: 'table listing slot-manager-showing-parent'}, [
            D.thead({}, [
              D.th({className: 'slot-manager-parent-location'}, [
                D.span({ className: 'slot-manager-location-label' }, 'Location: '),
                that.renderLinkedPath(effective_tile.path)
              ]),
            ]),
            D.tbody({}, effective_tile.data.map(function(tile, idx){
              return D.tr({}, D.td({}, [
                idx + 1,
                ': ',
                tile.label
              ]));
            }))
          ]));
        });
        if(showParents.length > 0){
          content.push(D.div({ className: 'slot-manager-parents' }, [
            D.h3({}, 'Parent tiles'),
            showParents
          ]));
        }else{
          content.push(D.div({}, [
            D.p({ className: 'discreet'}, 'There are no tiles assign here.')
          ]));
        }
      }
      if(that.state.mode === 'show' || that.state.mode === 'add'){
        var inner = [];
        if(this.state.tiles.length > 0){
          inner.push(D.h3({}, [
            'Tiles rendered here',
          ]));
          inner.push(D.table({ className: 'listing table', style: { width: '100%'}}, [
            D.thead({}, [
              D.th({}, 'Tile'),
              D.th({}, 'Actions'),
            ]),
            D.tbody({}, this.state.tiles.map(function(tile, idx){
              return D.tr({}, [
                D.td({}, [
                  idx + 1,
                  ': ',
                  tile.label
                ]),
                D.td({}, [
                  D.a({ href: '#', className: 'btn btn-default icon-move-up',
                        onClick: that.moveUp.bind(this, idx) }, 'Up'),
                  D.a({ href: '#', className: 'btn btn-default icon-move-down',
                        onClick: that.moveDown.bind(this, idx) }, 'Down'),
                  D.a({ href: '#', onClick: that.editTile.bind(this, idx),
                        className: 'btn btn-default icon-edit' }, 'Edit'),
                  D.a({ href: '#', onClick: that.deleteTile.bind(this, idx),
                        className: 'btn btn-default icon-trash' }, 'Delete')
                ])
              ]);
            }))
          ]));
        }
        content.push(D.div({ className: 'slot-manager-render-here'}, [
          D.div({}, inner),
          D.div({ className: 'form-group'}, [
            D.label({ className: ''}, 'Select a Tile'),
            D.select({ onChange: this.addTileSelected, value: 'add' },
                   this.getAvailableSlots())
          ])
        ]));
      }
      return content;
    },

    getAvailableSlots: function(){
      var slots = [D.option({ value: 'add'}, 'Select Tile...')];
      var available = $('body').attr('data-available-slots');
      if(available){
        available = $.parseJSON(available);
        _.each(_.keys(available).sort(), function(groupName){
          var items = [];
          var tiles = _.sortBy(available[groupName], function(tile){
            return tile.label;
          });
          _.each(tiles, function(tile){
            items.push(D.option({value: tile.id}, tile.label));
          });
          slots.push(D.optgroup({ label: groupName}, items));
        });
      }else{
        slots.push(D.optgroup({ label: 'Structure'}, [
          D.option({value: 'plone.app.standardtiles.rawhtml'}, 'Text'),
        ]));
      }
      return slots;
    },

    clickSelected: function(selected, e){
      e.preventDefault();
      this.state.selected = selected;
      this.doAction({});
    },

    renderMode: function(){
      var that = this;
      var options = [];
      if(that.state.current !== '/'){
        options.push(D.label({className: 'checkbox-inline'}, [
          D.input({ type: 'radio', name: 'slotMode', value: 'parent',
                    checked: that.state.mode == 'parent', onClick: that.modeClicked }),
          'Inherit'
        ]));
      }
      options.push(D.label({ className: 'checkbox-inline'}, [
        D.input({ type: 'radio', name: 'slotMode', value: 'hide',
                  checked: that.state.mode == 'hide', onClick: that.modeClicked }),
        'Hide'
      ]));
      options.push(D.label({className: 'checkbox-inline'}, [
        D.input({ type: 'radio', name: 'slotMode', value: 'show',
                  checked: that.state.mode == 'show', onClick: that.modeClicked }),
        'Replace'
      ]));
      options.push(D.label({className: 'checkbox-inline'}, [
        D.input({ type: 'radio', name: 'slotMode', value: 'add',
                  checked: that.state.mode == 'add', onClick: that.modeClicked }),
        'Add'
      ]));
      return D.div({ className: 'form-group radio-group slot-manager-display-mode'}, [
        D.label({ }, 'Display Mode'),
        D.div({ className: 'radio' }, options)
      ]);
    },

    cancelEdit: function(callback){
      var that = this;
      var data = {
        action: 'cancelcopy',
        metaId: that.props.slot.id,
        _authenticator: utils.getAuthenticator()
      };
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-portal-url') + that.state.current + '/@@meta-tile-manager',
        data: data
      }).done(function(){
        callback();
      }).always(function(){
        utils.loading.hide();
      }).fail(function(){
        alert('Unknown error');
      });
    },

    editRoot: function(e){
      e.preventDefault();
      var that = this;
      // that.cancelEdit(function(){
        that.setState({
          current: '/'
        }, function(){
          that.props.slot.workingId = undefined;
          that.startEditing();
        });
      // });
    },

    editHomepage: function(e){
      e.preventDefault();
      var that = this;
      // that.cancelEdit(function(){
        that.setState({
          current: '/' + that.props.defaultPage,
        }, function(){
          that.props.slot.workingId = undefined;
          that.startEditing();
        });
      // });
    },

    renderCurrentLocation: function(){
      var that = this;
      var extra = '';
      if(that.state.current === '/' + that.props.defaultPage){
        extra = D.div({ className: "portalMessage info" }, [
          D.strong({}, 'Info'),
          ' You are managing slots from the home page of the site. ',
          D.a({ href: '#', onClick: that.editRoot }, 'Click here'),
          ' to manage slots that apply to the entire site. '
        ]);
      }else if(that.state.current === '/'){
        extra = D.div({ className: "portalMessage info" }, [
          D.strong({}, 'Info'),
          ' You are managing slots from the root of the site. ',
          D.a({ href: '#', onClick: that.editHomepage }, 'Click here'),
          ' to manage slots that only apply at the homepage. '
        ]);
      }
      return D.div({ className: 'castle-slot-location-container' }, [
        extra,
        D.div({ className: 'input-group location'}, [
          D.span({ className: 'input-group-addon' }, 'Location'),
          D.span({ className: 'form-control' }, that.state.current)
        ])
      ]);
    },

    render: function(){
      var that = this;
      return D.div({ className: 'castle-slots'},[
        that.renderCurrentLocation(),
        that.renderMode(),
        that.renderTileListing()
      ]);
    },
    getDefaultProps: function(){
      return {
        slot: {},
        defaultPage: $('body').attr('data-site-default')
      };
    }
  });

  var SlotManagerModalComponent = cutils.Class([Modal], {
    getInitialState: function(){
      return {
        slot: null,
        layout: null
      };
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'slot-manager-modal',
        title: 'Choose slot to manage',
        slots: []
      });
    },

    // on select... title: 'Manage ' + slot.replace('meta-', '') + ' slot', tileId: slot

    componentDidMount: function(){
      var that = this;
      Modal.componentDidMount.apply(that);
      var $el = that.getModalEl();
      $el.on('hidden.bs.modal', function(){
        if(that.refs.manager.state.dirty){
          window.location.reload();
        }
      });
      //   if(that.refs.manager && that.refs.manager.state.dirty){
      //     if(confirm('Do you want to save your changes?')){
      //       that.saveEditClicked();
      //     }else{
      //       that.cancelEditClicked();
      //     }
      //   }
      // });

      // prevent weird draft support issues...
      var path = $.cookie('plone.app.drafts.path');
      if(path){
        $.removeCookie('plone.app.drafts.path', {path: path});
        $.removeCookie('plone.app.drafts.draftName', {path: path});
        $.removeCookie('plone.app.drafts.targetKey', {path: path});
        $.removeCookie('plone.app.drafts.userId', {path: path});
      }
      that.bindIframe();
    },
    componentDidUpdate: function(){
      this.bindIframe();
    },

    bindIframe: function(){
      var that = this;
      if(!that.refs.iframe){
        return;
      }

      var $iframe = $(that.refs.iframe.getDOMNode());
      $iframe.load(function(){
        var newHeight = 0;
        $iframe.contents().find('body > *').each(function(){
          newHeight += $(this).height();
        });
        $iframe.height(newHeight);
        $('.castle-tile-container', $iframe.contents()).off('click').on('click', function(){
          var $el = $(this);
          that.props.title = 'Manage ' + $el.attr('data-tile-title') + ' Slot';
          that.setState({
            slot: {
              id: $el.attr('data-tile-id'),
              title: $el.attr('data-tile-title')
            }
          });
        });
      });
    },

    renderContent: function(){
      var that = this;
      if(that.state.slot){
        return R.createElement(SlotManagerComponent, {
          slot: this.state.slot,
          key: that.state.slot.id,
          ref: 'manager'});
      }else{
        return D.div({ className: 'slot-chooser'}, [
          D.p({ className: 'discreet'}, 'Slots are areas in the theme where you can place tiles into that are outside the main content area.'),
          D.iframe({ src: $('body').attr('data-portal-url') + '/@@render-slots-site-layout?layout=' + $('body').attr('data-site-layout'),
                     width: '100%', style: {'min-height': '400px'}, className: 'castle-slot-selector', ref: 'iframe', name: 'choose_slot'})
        ]);
      }
    },

    cancelEditClicked: function(e, forced){
      var that = this;
      if(e){
        e.preventDefault();
      }
      if(!that.refs.manager){
        return that.setState({
          slot: null
        });
      }
      var state = that.refs.manager.state;

      if(!forced){
        // check if the user really wants to lose changes
        if(!confirm("You have unsaved changes. Are you certain you want to cancel those changes?")){
          return;
        }
      }
      var data = {
        action: 'cancelcopy',
        metaId: that.state.slot.id,
        _authenticator: utils.getAuthenticator()
      };
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-portal-url') + state.current + '/@@meta-tile-manager',
        data: data
      }).done(function(){
        that.refs.manager.state.dirty = false;
        that.setState({
          slot: null
        });
      }).always(function(){
        utils.loading.hide();
      });
    },

    saveEditClicked: function(e){
      var that = this;
      if(e){
        e.preventDefault();
      }
      if(!that.refs.manager){
        return that.hide();
      }
      var state = that.refs.manager.state;

      var data = {
        action: 'savecopy',
        metaId: that.state.slot.id,
        _authenticator: utils.getAuthenticator()
      };
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-portal-url') + state.current + '/@@meta-tile-manager',
        data: data
      }).done(function(){
        that.refs.manager.state.dirty = false;
        that.hide();
        window.location.reload();
      }).always(function(){
        utils.loading.hide();
      }).fail(function(){
        alert('Error saving slot changes.');
      });
    },

    renderFooter: function(){
      var that = this;
      var buttons = [];
      if(that.state.slot){
        buttons.push(D.button({
          type: 'button', className: 'plone-btn plone-btn-primary pull-right',
          onClick: that.saveEditClicked }, 'Save'));
        // buttons.push(D.button({ type: 'button', className: 'plone-btn plone-btn-default pull-right',
        //                         onClick: that.cancelEditClicked }, 'Cancel'));
      } else {
        buttons.push(D.button({ type: 'button', className: 'plone-btn plone-btn-default pull-right',
                                onClick: that.hide}, 'Close'));
      }
      return D.div({}, buttons);
    }
  });

  return SlotManagerModalComponent;
});
