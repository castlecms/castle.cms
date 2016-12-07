/* global define */

/* notes on implementation!

  To the user, layout is now *design*
  but all backend related info, layout stays layout in terms of functionality
*/

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/modal',
  'castle-url/components/utils'
], function($, Base, _, R, utils, Modal, cutils) {
  'use strict';
  var D = R.DOM;

  var DesignModalComponent = cutils.Class([Modal], {
    getInitialState: function(){
      return {
        loading: true,
        available: [],
        applied: null,
        context: null,
        applied_context: null,
        page_layout: null,
        section_layout: null,
        folder: null,
        dirtyPage: false,
        dirtySection: false
      };
    },
    componentDidMount: function(){
      utils.loading.show();
      var that = this;
      Modal.componentDidMount.apply(this);
      $.ajax({
        url: $('body').attr('data-base-url') + '/@@page-layout-selector'
      }).done(function(data){
        if(!data.available[data.page_layout]){
          data.page_layout = null;
        }
        data.original_page_layout = data.page_layout;
        data.original_applied_context = data.applied_context;
        data.original_applied = data.applied;
        that.setState(data);
      }).fail(function(){
        alert('error loading design data');
      }).always(function(){
        utils.loading.hide();
      });
    },

    renderSelected: function(){
      var selectedName = this.state.available[this.state.applied];
      if(!selectedName){
        selectedName = 'Default';
      }
      var selected = D.span({ className: 'selected-design default'}, 'Default site design');

      if(this.state.applied_context !== '/'){
        if(this.state.applied_context !== this.state.context){
          selected = D.span({ className: 'selected-design'}, [
            '"' + selectedName + '" applied from ',
            D.span({ className: 'selected-design-path'}, this.state.applied_context),
          ]);
        }else{
          selected = D.span({ className: 'selected-design'}, selectedName);
        }
      }
      return D.p({ className: 'selected-design-container'}, [
        D.span({ className: 'selected-design-label'}, 'Selected Design'),
        ': ',
        selected
      ]);
    },

    renderAvailableOptions: function(){
      var that = this;
      var options = [
        D.option({ value: ''}, ' - Use parent setting'),
        D.option({ value: 'index.html'}, 'Default')
      ];
      _.keys(this.state.available).sort().forEach(function(id){
        if(id === 'index.html'){
          return;
        }
        options.push(D.option({ value: id }, that.state.available[id]));
      });
      return options;
    },

    pageChanged: function(e){
      if(!e.target.value && this.state.dirtyPage){
        // revert
        this.setState({
          page_layout: this.state.original_page_layout,
          applied_context: this.state.original_applied_context,
          applied: this.state.original_applied
        });
      }else{
        this.setState({
          page_layout: e.target.value,
          applied_context: this.state.context,
          applied: e.target.value,
          dirtyPage: true
        });
      }
    },

    renderPageSelection: function(){
      return D.div({ className: 'form-group'}, [
        D.label({}, [
          'Page Design',
          D.span({ className: 'formHelp'}, 'Design that will be applied to this page only.')
        ]),
        D.select({ className: 'form-control', value: this.state.page_layout,
                   onChange: this.pageChanged}, this.renderAvailableOptions())
      ]);
    },

    sectionChanged: function(e){
      this.setState({
        section_layout: e.target.value,
        dirtySection: true
      });
    },

    renderSectionSelection: function(){
      return D.div({ className: 'form-group'}, [
        D.label({}, [
          'Section Design',
          D.span({ className: 'formHelp'}, 'Design that will be applied to all pages inside this folder.')
        ]),
        D.select({ className: 'form-control', value: this.state.section_layout,
                   onChange: this.sectionChanged}, this.renderAvailableOptions())
      ]);
    },

    renderContent: function(){
      var that = this;
      return D.div({ className: 'castle-design-container'}, [
        that.renderSelected(),
        that.renderPageSelection(),
        that.renderSectionSelection()
      ]);
    },

    saveClicked: function(e){
      e.preventDefault();
      utils.loading.show();
      var that = this;
      $.ajax({
        url: $('body').attr('data-base-url') + '/@@page-layout-selector',
        type: 'POST',
        data: {
          action: 'save',
          _authenticator: utils.getAuthenticator(),
          data: JSON.stringify(this.state)
        }
      }).done(function(data){
        if(!data.success){
          return alert('Error saving design change');
        }
        if(that.state.dirtyPage){
          window.location.reload();
        }else{
          that.hide();
        }
      }).fail(function(){
        alert('error loading design data');
      }).always(function(){
        utils.loading.hide();
      });
    },

    renderFooter: function(){
      var buttons = [
        D.button({ type: 'button', className: 'plone-btn plone-btn-default',
                   onClick: this.hide}, 'Cancel'),
        D.button({ type: 'button', className: 'plone-btn plone-btn-primary',
                   onClick: this.saveClicked,
                   disabled: !this.state.dirtyPage && !this.state.dirtySection}, 'Save')];
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'design-modal',
        title: 'Design'
      });
    }
  });

  return DesignModalComponent;
});
