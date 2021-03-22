console.log('why am i being called?')

/* global require */

require([
    'jquery',
    'underscore',
    'mockup-patterns-structure',
    'mockup-patterns-structure-url/js/views/app',
    'mockup-patterns-structure-url/js/views/paging',
    'pat-registry',
    'text!castle-url/patterns/structure/paging.xml',
  ], function(
      $,
      _,
      Structure,
      AppView,
      PagingTemplate,
      registry,
      PagingView
    ) {
    'use strict';
  

    // unregister existing pattern
    delete registry.patterns.structure;
    delete $.fn.patStructure;


    // util stuff
    var MAX_BATCH_SIZE = '100000';
    function totalPagesExists(){
        return totalPages && totalPages === parseInt(totalPages, 10);
    }
    function currentPageExists(){
        return currentPage && currentPage === parseInt(currentPage, 10);
    }
    function pagesExist(){
        return currentPageExists() && totalPagesExists();
    }

    // modify PagingView
    PagingView.template = _.template(PagingTemplate);
    PagingView.nextResultPage = function(e) {
        e.preventDefault();
        if (pagesExist() && currentPage >= totalPages) {
            return;
        }
        this.collection.requestNextPage();
      };
    PagingView.changeCount = function(e){
        e.preventDefault();
        var text = $(e.target).text();
        var per = text === 'All' ? MAX_BATCH_SIZE : text;
        this.collection.howManyPer(per);
        this.app.setCookieSetting('perPage', per);
    };


    // creating new pattern automatically registers it
    Structure.extend({
      name: 'structure',
      trigger: '.pat-structure',
      parser: 'mockup',
      init: function() {
        var self = this;
  
        /*
          This part replaces the undefined (null) values in the user
          modifiable attributes with the default values.
  
          May want to consider moving the _default_* values out of the
          options object.
        */
        var replaceDefaults = ['attributes', 'activeColumns', 'availableColumns', 'buttons', 'typeToViewAction'];
        _.each(replaceDefaults, function(idx) {
          if (self.options[idx] === null) {
            self.options[idx] = self.options['_default_' + idx];
          }
        });
  
        var mergeDefaults = ['tableRowItemAction'];
        _.each(mergeDefaults, function(idx) {
          var old = self.options[idx];
          self.options[idx] = $.extend(
            false, self.options['_default_' + idx], old
          );
        });
  
        self.browsing = true; // so all queries will be correct with QueryHelper
        self.options.collectionUrl = self.options.vocabularyUrl;
        self.options.pattern = self;
  
        // the ``attributes`` options key is not compatible with backbone,
        // but queryHelper that will be constructed by the default
        // ResultCollection will expect this to be passed into it.
        self.options.queryHelperAttributes = self.options.attributes;
        delete self.options.attributes;
  
        self.view = new AppView(self.options);
        self.view.pagingView = new PagingView({app: self.view});

        self.$el.append(self.view.render().$el);
      }
    });
  
  });