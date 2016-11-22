/*
XXX
this is a work-in-progress
*not* active
*/
/* Querystring pattern.
 *
 * Options:
 *    criteria(object): options to pass into criteria ({})
 *    indexOptionsUrl(string): URL to grab index option data from. Must contain "sortable_indexes" and "indexes" data in JSON object. (null)
 *    previewURL(string): URL used to pass in a plone.app.querystring-formatted HTTP querystring and get an HTML list of results ('portal_factory/@@querybuilder_html_results')
 *    previewCountURL(string): URL used to pass in a plone.app.querystring-formatted HTTP querystring and get an HTML string of the total number of records found with the query ('portal_factory/@@querybuildernumberofresults')
 *    classWrapperName(string): CSS class to apply to the wrapper element ('querystring-wrapper')
 *    classSortLabelName(string): CSS class to apply to the sort on label ('querystring-sort-label')
 *    classSortReverseName(string): CSS class to apply to the sort order label and checkbox container ('querystring-sortreverse')
 *    classSortReverseLabelName(string): CSS class to apply to the sort order label ('querystring-sortreverse-label')
 *    classPreviewCountWrapperName(string): TODO ('querystring-previewcount-wrapper')
 *    classPreviewResultsWrapperName(string): CSS class to apply to the results wrapper ('querystring-previewresults-wrapper')
 *    classPreviewWrapperName(string): CSS class to apply to the preview wrapper ('querystring-preview-wrapper')
 *    classPreviewName(string): CSS class to apply to the preview pane ('querystring-preview')
 *    classPreviewTitleName(string): CSS class to apply to the preview title ('querystring-preview-title')
 *    classPreviewDescriptionName(string): CSS class to apply to the preview description ('querystring-preview-description')
 *    classSortWrapperName(string): CSS class to apply to the sort order and sort on wrapper ('querystring-sort-wrapper')
 *    showPreviews(boolean): Should previews be shown? (true)
 *
 * Documentation:
 *    # Default
 *
 *    {{ example-1 }}
 *
 *    # Without Previews
 *
 *    {{ example-2 }}
 *
 * Example: example-1
 *    <input class="pat-querystring"
 *           data-pat-querystring="indexOptionsUrl: /tests/json/queryStringCriteria.json" />
 *
 * Example: example-2
 *    <input class="pat-querystring"
 *           data-pat-querystring="indexOptionsUrl: /tests/json/queryStringCriteria.json;
 *                                 showPreviews: false;" />
 *
 */


define([
  'jquery',
  'pat-base',
  'castle-url/libs/react/react.min',
  'castle-url/patterns/querystring/querystring',
  'castle-url/patterns/querystring/store'
], function($, Base, R, QueryStringComponent, StorageFactory) {
  'use strict';

  var QueryString = Base.extend({
    name: 'querystring',
    trigger: '.pat-querystring',
    parser: 'mockup',
    defaults: {
      indexes: [],
      classWrapperName: 'querystring-wrapper',
      criteria: {},
      indexOptionsUrl: null,
      previewURL: 'portal_factory/@@querybuilder_html_results', // base url to use to request preview information from
      previewCountURL: 'portal_factory/@@querybuildernumberofresults',
      classSortLabelName: 'querystring-sort-label',
      classSortReverseName: 'querystring-sortreverse',
      classSortReverseLabelName: 'querystring-sortreverse-label',
      classPreviewCountWrapperName: 'querystring-previewcount-wrapper',
      classPreviewResultsWrapperName: 'querystring-previewresults-wrapper',
      classPreviewWrapperName: 'querystring-preview-wrapper',
      classPreviewName: 'querystring-preview',
      classPreviewTitleName: 'querystring-preview-title',
      classPreviewDescriptionName: 'querystring-preview-description',
      classSortWrapperName: 'querystring-sort-wrapper',
      classAddCriteriaName: 'querystring-add-criteria-wrapper',
      showPreviews: true
    },
    init: function() {
      var self = this;

      // hide input element
      self.$el.hide();

      // create wrapper for out criteria
      self.$wrapper = $('<div/>');
      self.$el.after(self.$wrapper);

      // initialization can be detailed if by ajax
      self.initialized = false;

      self.findRelatedFields();

      if (self.options.indexOptionsUrl) {
        $.ajax({
          url: self.options.indexOptionsUrl,
          success: function(data) {
            self.options.indexes = data.indexes;
            self.options['sortable_indexes'] = data['sortable_indexes']; // jshint ignore:line
            self._init();
          },
          error: function(xhr) {
            // XXX handle this...
          }
        });
      } else {
        self._init();
      }
    },

    findRelatedFields: function(){
      var that = this;
      that.$originalSortOn = that.$originalReversed = null;
      var $form = that.$el.closest('form');
      if($form.size() === 0){
        return;
      }
      var $sortOn = $('input[id*="-sort_on"]', $form);
      if($sortOn.size() > 0){
        that.$originalSortOn = $sortOn;
        that.$originalSortOn.closest('.field').hide();
      }
      var $reversed = $('input[id*="-sort_reversed"]', $form);
      if($reversed.size() > 0){
        that.$originalReversed = $reversed;
        that.$originalReversed.closest('.field').hide();
      }
    },

    _init: function() {
      var that = this;
      that.timer = null;

      that.reversedValue = false;
      that.sortOnValue = false;

      this.storage = StorageFactory();
      this.options.storage = this.storage;

      that.options.afterChange = function(){
        if(that.timer){
          clearTimeout(that.timer);
        }
        that.timer = setTimeout(function(){
          if(that.sortOnValue !== that.component.state.sortOn){
            that.$sortOn.trigger('change');
          }
          if(that.reversedValue !== that.component.state.reversed){
            that.$sortOrder.trigger('change');
          }
          that.$el.val(JSON.stringify(that.component.getQueryString()));
          that.$el.trigger('change');
          that.reversedValue = that.component.state.reversed;
          that.sortOnValue = that.component.state.sortOn;

          if(that.$originalSortOn){
            that.$originalSortOn.val(that.sortOnValue);
            that.$originalSortOn.trigger('change');
          }
          if(that.$originalReversed){
            that.$originalReversed[0].checked = that.reversedValue;
            that.$originalReversed.trigger('change');
          }
        }, 300);
      };

      var component = R.render(
        R.createElement(QueryStringComponent, this.options), this.$wrapper[0]
      );

      that.component = that.$el[0].component = component;
      that.$sortOn = $(that.component.refs.sortOn.refs.select.getDOMNode());
      that.$sortOrder = $(that.component.refs.sortOrder.getDOMNode());

      // check if it has initial values...
      var data = {};
      var value = that.$el.val();
      if(value){
        try{
          data.criterias = JSON.parse(value);
        }catch(e){}
      }
      if(that.$originalSortOn){
        data.sortOn = that.$originalSortOn.val();
      }
      if(that.$originalReversed){
        data.reversed = that.$originalReversed[0].checked;
      }
      that.storage.store.setData(data);
      component.setState(data);

      that.$el.trigger('initialized', that);
    }
  });

  return QueryString;

});
