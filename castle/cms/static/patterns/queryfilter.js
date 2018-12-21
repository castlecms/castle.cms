/* global define */

define([
  'jquery',
  'pat-base',
  'mockup-utils',
  'castle-url/libs/react/react.min',
  'underscore',
  'pat-registry'
], function($, Base, utils, R, _, Registry) {
  'use strict';

  var D = R.DOM;

  var trackUrl = function(url){
    var anchor = document.createElement('a');
    anchor.href = url;
    var trackValue = anchor.pathname + anchor.search;
    if(window.ga){
      window.ga('send', 'pageview', trackValue);
    }
    if(window._paq){
      window._paq.push([
        'trackEvent', 'queryfilter', trackValue]);
    }
  };

  var QueryFilterComponent = R.createClass({
    getInitialState: function(){
      var self = this;
      var subject = [];
      var tags = [];
      return $.extend({}, true, {
         SearchableText: '',
         Subject: subject,
         selectedTags: [],
         singleFilter: false,
         sort_on: '',
         searchedText: '',
         'selected-year': '',
         loading: false
      }, this.props.query);
    },
    getDefaultProps: function(){
      return {
        tags: [],
        ajaxResults: false,
        query: {}
      };
    },
    valueChange: function(attr, e){
      this.state[attr] = e.target.value;
      this.state.singleFilter = false;
      this.forceUpdate();
    },
    tagSelected: function(e){
      var self = this;
      // Subject = the terms being searched for
      // seletedTags = the tags displayed below the filter
      // The tags can be enabled/disabled so we need to
      // keep track of both
      var subject = self.state.Subject;
      var tags = self.state.selectedTags;

      subject.push(e.target.value);
      tags.push(e.target.value);

      self.setState({
        Subject: subject,
        selectedTags: tags,
        singleFilter: false
      }, self.filterClicked);
    },
    getActive: function(type, value) {
      var self = this;
      var filter = self.state.singleFilter;

      var filter_types = {'text': 'Title', 'tag': 'Subject'};
      if( !filter ) {
        return;
      }

      var filter_type = filter_types[type];

      if( filter.name != filter_type ) {
        return;
      }

      if( filter.value != value ) {
        return;
      }

      return 'active';

    },
    removeFilter: function(tag, e){
      var self = this;
      // The user clicked the X next to a tag,
      // Remove the tag and re-fetch results
      e.preventDefault();

      var subject = self.state.Subject;
      var tags = self.state.selectedTags;

      var index = subject.indexOf(tag);
      var tag_index = tags.indexOf(tag);

      if (index > -1) {
        subject.splice(index, 1);
        tags.splice(tag_index, 1);
      }
      self.setState({
        Subject: subject,
        selectedTags: tags,
        singleFilter: false
      }, this.filterClicked);
    },
    clearFilter: function(e){
      var that = this;
      e.preventDefault();
      that.setState(that.getInitialState(), function(){
        that.filterClicked();
      });
    },
    hasFilters: function(){
      if(this.state.searchedText || this.state['selected-year'] || this.state.Subject.length > 0){
        return true;
      }else{
        return false;
      }
    },
    fetchResults: function() {
      var self = this;
      if(self.props.ajaxResults){
        self.state.loading = true;
        utils.loading.show();
        var formData = [];
        if(self.state.sort_on){
          formData.push({name: 'sort_on', value: self.state.sort_on});
        }
        if( self.state.singleFilter ) {
          // We've clicked on a filter bubble, and only want
          // to search based on that, BUT still want the bubbles to appear
          formData.push(self.state.singleFilter);
        }else{
          if(self.state.SearchableText){
            // actually searching Title here...
            formData.push({name: 'Title', value: self.state.SearchableText});
          }
          if(self.state['selected-year']){
            formData.push({name: 'selected-year', value: self.state['selected-year']});
          }

          self.state.Subject.forEach(function(tag){
            formData.push({name: 'Subject', value: tag});
          });
        }

        var url = self.props.ajaxResults.url;
        if(url.indexOf('?') === -1){
          url += '?';
        }else {
          url += '&';
        }
        url += $.param(formData);
        self.props.pattern.setAjaxUrl(url);
        $.ajax({
          url: url
        }).done(function(data){
          var $dom = $(utils.parseBodyTag(data));
          var $content = $(self.props.ajaxResults.selector, $dom);
          $(self.props.ajaxResults.selector).replaceWith($content);
          Registry.scan($content);
          self.props.pattern.bind();
          self.setState({
            searchedText: self.state.SearchableText,
            loading: false
          });
          // parse url
          trackUrl(url);
        }).always(function(){
          utils.loading.hide();
          self.state.loading = false;
        }).fail(function(){
          alert('error getting query results.');
        });
      }
    },
    filterClicked: function(e){
      if(e){
        e.preventDefault();
      }

      this.fetchResults();
    },
    toggleFilter: function(e){
      var self = this;
      var val = e.target.text;
      var filter = self.state.singleFilter;
      var classlist = e.target.classList;
      var name = '';

      if( classlist.contains('filter-tag') ) {
        name = 'Subject';
      }else if( classlist.contains('filter-text') ) {
        name = 'Title';
      }

      // We're disabling the selected filter
      if( filter && filter.name == name && filter.value == val ) {
        self.setState({
          singleFilter: false
        }, self.filterClicked);
      }else{

        // 'singleFilter' imitates the params passed into the formData
        // array in fetchResults
        self.setState({
          singleFilter: {
            name: name,
            value: val
          }
        }, self.filterClicked);
      }
    },
    render: function(){
      var self = this;
      var fields = [];
      var widgetCount = 1;

      if(self.props.tags.length > 0){
        widgetCount += 1;
        fields.push(D.div({ className: 'field-wrapper' }, [
          D.label({ htmlFor: 'select-categories' }, 'Filter by '),
          D.select({ type: 'text', id: 'select-categories', onChange: this.tagSelected, value: ''},
            [D.option({value: ''}, 'Categories')].concat(_.difference(self.props.tags, self.state.Subject).map(function(tag){
              return D.option({value: tag}, tag);
            })))
        ]));
        fields.push(D.span({ className: 'and' }, ' and '));
      }
      fields.push(D.div({ className: 'field-wrapper' }, [
        D.label({ htmlFor: 'filter-input' }, ' Search for '),
        D.input({ type: 'text', name: 'SearchableText',
                  placeholder: 'Search for...', id: 'filter-input', value: this.state.SearchableText,
                  onChange: this.valueChange.bind(this, 'SearchableText')})
      ]));

      if(self.props.yearFilter){
        widgetCount += 1;
        var options = [D.option({}, 'Year')];
        _.range(2010, (new Date()).getFullYear() + 1).forEach(function(year){
          options.push(D.option({ value: year }, year));
        });
        fields.push(D.div({ className: 'field-wrapper' }, [
          D.label({ htmlFor: 'filter-year' }, 'Filter by'),
          D.select({ name: 'year', id: 'filter-year', value: self.state['selected-year'],
                     onChange: this.valueChange.bind(this, 'selected-year')}, options)
        ]));
      }

      var filters = [];

      filters = this.state.selectedTags.map(function(tag){
        return D.li({
          className: self.getActive('tag', tag)
        }, [
          D.a({
            className: 'filter filter-tag',
            onClick: self.toggleFilter}, tag),
          D.span({
            className: 'glyphicon glyphicon-remove-sign',
            onClick: self.removeFilter.bind(self, tag)
          })
        ]);
      });

      if(this.state.searchedText){
        filters.push(D.li({
          className: self.getActive('text', self.state.searchedText)
        }, [
          D.a({
            className: 'filter filter-text',
            onClick: this.toggleFilter
          }, this.state.searchedText),
          D.span({
            className: 'glyphicon glyphicon-remove-sign',
            onClick: function(e){
                e.preventDefault();
                self.setState({
                  SearchableText: '',
                  searchedText: '',
                  singleFilter: false
                }, function(){
                  self.filterClicked();
                });
              }})
        ]));
      }
      if(self.state['selected-year']){
        filters.push(D.li({
          className: 'filter-year',
          onClick: self.toggleFilter
        }, [
          this.state['selected-year'],
          D.button({ className: 'remove',
                onClick: function(e){
                  e.preventDefault();
                  self.setState({
                    'selected-year': ''
                  }, function(){
                    self.filterClicked();
                  });
                }}, 'x')
        ]));
      }

      fields.push(D.button({ type: 'submit', onClick: this.filterClicked, className: 'pull-right plone-btn plone-btn-default'}, 'Filter'));
      fields.push(D.div({ className: 'clearfix'}));

      var filter_box = D.div({className: 'filter-fields'}, fields);

      return D.form({ ref: 'form', className: 'queryfilter-container field-count-' + widgetCount}, [
        filter_box,
        D.div({ className: 'row'}, [
          D.div({className: 'col-md-9 filters'}, [
            D.ul({ className: 'filter-list'}, filters),
            [
              this.hasFilters() &&
              D.button({
                className: 'clear',
                onClick: this.clearFilter, style: { cursor: 'pointer'}
              }, 'Clear') || ''
            ]
          ]),
          D.div({className: 'col-md-3 sort-by'}, [
            D.label({ htmlFor: 'select-sort-by' }, 'Sort by:'),
            D.select({ name: 'sort_on', id: 'select-sort-by', onChange: this.valueChange.bind(this, 'sort_on')}, [
              D.option({ value: 'effective'}, 'Newest'),
              D.option({ value: 'created'}, 'Created'),
              D.option({ value: 'modified'}, 'Modified')
            ])
          ])
        ])
      ]);
    }
  });

  var QueryFilter = Base.extend({
    name: 'queryfilter',
    trigger: '.pat-queryfilter',
    parser: 'mockup',
    defaults: {
      tags: [],
      query: {},
      selector: null,
      yearFilter: false
    },
    init: function() {
      var self = this;
      var opts = $.extend({}, true, self.options, {
        pattern: self
      });
      self.component = R.render(R.createElement(QueryFilterComponent, opts), this.$el[0]);
      self.setAjaxUrl(self.options.ajaxResults.url);
      self.bind();

      if($(self.options.ajaxResults.selector + ' .infinity').size() > 0){
        self.infinitHandler();
      }
    },

    setAjaxUrl: function(url){
      this.ajaxUrl = url;
    },

    infinitHandler: function(){
      if($('.template-edit,.mosaic-enabled').size() > 0){
        // not active here...
        return;
      }
      var that = this;
      var timeout;
      $(window).on('scroll', function(){
        clearTimeout(timeout);
        timeout = setTimeout(function(){
          if(that.component.state.loading){
            return;
          }
          var $moreBtn = $(that.options.ajaxResults.selector + ' .load-more');
          if($moreBtn.size() === 0){
            return;
          }
          var docViewTop = $(window).scrollTop();
          var docViewBottom = docViewTop + $(window).height();

          var elemTop = $moreBtn.offset().top;
          var elemBottom = elemTop + $moreBtn.height();

          if(elemBottom <= docViewBottom){
            // and we're visible;
            $moreBtn.trigger('click');
          }
        }, 100);
      });
    },

    bind: function(){
      var self = this;
      var selector = self.options.ajaxResults.selector;
      var $results = $(selector);
      $('.load-more', $results).off('click').on('click', function(e){
        var url = self.ajaxUrl;
        if(url.indexOf('?') !== -1){
          url += '&';
        }else{
          url += '?';
        }
        url += 'page=' + $(this).attr('data-page');

        e.preventDefault();
        utils.loading.show();
        $.ajax({
          url: url
        }).done(function(data){
          var $dom = $(data);
          $(selector + ' .top-total').replaceWith(
            $(selector + ' .top-total', $dom));
          $(selector + ' .bottom-total').replaceWith(
            $(selector + ' .bottom-total', $dom));
          var $contents = $(selector + ' ul,' + selector + ' .query-listing-container');
          var $items = $(selector + ' ul li,' + selector + ' .query-listing-container > *', $dom);
          $contents.append($items);
          if($contents.hasClass("pat-masonry")){
            var masonryPattern = $contents.data('pattern-masonry');
            if(masonryPattern){
              masonryPattern.addItems($items);
            }
          }
          Registry.scan($items);
          self.bind();

          trackUrl(url);
        }).always(function(){
          utils.loading.hide();
        }).fail(function(){
          alert('error getting query results.');
        });
      });
    }
  });

  return QueryFilter;

});
