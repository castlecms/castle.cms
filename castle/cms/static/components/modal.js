/* jshint quotmark: false */


define([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-patterns-modal',
  'mockup-utils',
  'castle-url/libs/bootstrap/js/modal'
], function($, R, PloneModal, utils) {
  'use strict';

  /* XXX with escape keys, need one place to manage all the overlays and escaping them.
     This is nasty and requires escape key by default being off for plone modal */
  if(PloneModal && PloneModal.prototype._hide === undefined){
    PloneModal.prototype._hide = PloneModal.prototype.hide;
    PloneModal.prototype.hide = function(){
      var $modalWrapper = this.$modal.closest('.plone-modal-wrapper');
      var thisZIndex = parseInt($modalWrapper.css('zIndex'));
      var $modals = $(".plone-modal-wrapper:visible,.modal-open .castle-modal-wrapper .modal:visible");
      if($modals.size() > 1 && $.mosaic && $.mosaic.overlay && $.mosaic.overlay.app){
        // make sure this isn't the top-most one
        var maxZIndex = 0;
        $modals.each(function(){
          var zIndex = parseInt($(this).css('zIndex'));
          if(zIndex > maxZIndex){
            maxZIndex = zIndex;
          }
        });
        // skip out here, we'll close when it's the last one
        if(maxZIndex > thisZIndex){
          return;
        }
      }
      PloneModal.prototype._hide.apply(this, []);
    };
  }

  $(document).keyup(function(e) {
    if (e.keyCode == 27) {
      // need to find the top most modal that is currently open
      utils.loading.hide();
      var max = 0;
      var $found;
      $(".plone-modal-wrapper:visible,.modal-open .castle-modal-wrapper .modal:visible").each(function(){
        var zIndex = parseInt($(this).css('zIndex')) + 0;
        if(zIndex > max){
          max = zIndex;
          $found = $(this);
        }
      });
      if($found){
        if($found.hasClass('plone-modal-wrapper')) {
          if($found.hasClass('mosaic-overlay')){
            $.mosaic.overlay.close();
          }else {
            var pattern = $found.find('.plone-modal').data('pattern-plone-modal');
            if(pattern){
              pattern.hide();
            }
          }
        } else {
          $('button.close', $found).trigger('click');
        }
      }
    }
  });


  var D = R.DOM;
  var div = D.div;
  var button = D.button;
  var span = D.span;

  var Modal = {
    getInitialState: function(){
      return {
        zIndex: 3000,
        shown: false,
        preventClose: false
      };
    },

    show: function(){
      $(this.refs.modal.getDOMNode()).modal('show');
    },

    hide: function(e){
      if(e){
        e.preventDefault();
      }
      $(this.refs.modal.getDOMNode()).modal('hide');
    },

    getModalEl: function(){
      return $(this.refs.modal.getDOMNode());
    },

    componentDidMount: function() {
      var self = this;
      var $el = self.getModalEl();

      $el.on('shown.bs.modal', function(e){
        if(self.props.onShown){
          self.props.onShown(e, self);
        }
      });

      $el.on('show.bs.modal', function(){
        self.state.shown = true;
      });

      $el.modal(this.props.modalOptions);

      $el.on('hide.bs.modal', function(e){
        if(self.state.preventClose){
          e.preventDefault();
          return;
        }
        self.state.shown = false;
      });

      $el.on('hidden.bs.modal', function(e){
        if(self.props.onHidden){
          self.props.onHidden(e, self);
        }
        var $el = $(self.getDOMNode());
        if($('.castle-modal-wrapper,.plone-modal-wrapper').size() === 0){
          // otherwise, modals stick around...
          $('.plone-modal-backdrop').remove();
        }
        if($('.modal:visible').size() > 0){
          // need to re-add 'modal-open' class
          $('body').addClass('modal-open');
        }

        setTimeout(function(){
          // perform cleanup in delay because DOM node still may be necessary
          // for react to do some things and throw errors;
          $el.remove();
        }, 1000);
      });

      var zIndex = 3001;
      $(".plone-modal-wrapper,.plone-modal-backdrop,.modal-open .castle-modal-wrapper .modal").each(function(){
        zIndex = Math.max(zIndex, parseInt($(this).css('zIndex')) + 1 || 3001);
      });
      self.state.zIndex = zIndex;
      self.setModalZIndex();
    },

    componentDidUpdate: function(){
      this.setModalZIndex();
    },

    setModalZIndex: function(){
      $(this.refs.modal.getDOMNode()).css({'z-index': this.state.zIndex});
    },

    getId: function(){
      return this.props.id;
    },

    getTitle: function(){
      return this.props.title;
    },

    render: function(){
      var attrs = { ref: 'modal', className: 'modal fade'};
      var id = this.getId();
      if(id){
        attrs.id = id;
      }
      var modalStyles = {};
      if(this.props.width){
        modalStyles.width = this.props.width;
      }
      return div({ className: 'castle-modal-wrapper', ref: 'container' }, div(attrs, [
        div({ className: 'modal-dialog', style: modalStyles}, this.renderContentContainer())
      ]));
    },

    renderContentContainer: function(){
      return div({ className: 'modal-content' }, [
        div({ className: 'modal-header' }, this.renderHeader()),
        div({ className: 'modal-body'}, this.renderContent()),
        div({ className: 'modal-footer'}, this.renderFooter())
      ]);
    },

    renderHeader: function(){
      return [
        button({ type: 'button', className: 'close', onClick: this.hide }, [
          div({ className: 'close-button' }),
          span({ 'aria-hidden': 'true' }, '\u00d7')
        ]),
        D.h4({}, this.getTitle())
      ];
    },

    renderContent: function(){
      return div({});
    },

    renderFooter: function(){
      return '';
    },

    getDefaultProps: function(){
      return {
        id: null,
        title: 'Modal title',
        modalOptions: {
          backdrop: 'static',
          show: true
        },
        onHidden: function(){},
        onShown: function(){},
        width: null
      };
    }
  };

  return Modal;
});
