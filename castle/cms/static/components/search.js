/* global history */


require([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/utils',
  'moment'
], function($, R, utils, cutils, moment){
  'use strict';

  var HasHistory = !!window.history;

  function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
  }

  var D = R.DOM;
  var ContentTypeTranslations = {
    'application/pdf': 'PDF',
    'image': 'Image',
    'video': 'Video',
    'audio': 'Audio',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Spreadsheet',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Doc',
    'application/vnd.ms-powerpoint': 'Presentation',
    'application/msword': 'Doc',
    'application/vnd.ms-excel': 'Spreadsheet',
    'text/csv': 'Spreadsheet'
  };
  var DownloadableContentTypes = ['File', 'Video', 'Audio', 'Image', 'ExcelFile'];
  var SortOptions = [
    ['', 'Relevance'],
    ['effective', 'Publication Date'],
    ['modified', 'Modification Date'],
  ];

  var SearchResult = R.createClass({
    render: function(){
      var item = this.props;
      var ct = '';
      if(item.contentType){
        var mainType = item.contentType.split('/')[0];
        var ctname;
        if(ContentTypeTranslations[item.contentType]){
          ctname = ContentTypeTranslations[item.contentType];
        }else if(ContentTypeTranslations[mainType]){
          ctname = ContentTypeTranslations[item.contentType];
        }else if(item.portal_type === 'File'){
          ctname = 'File';
        }
        if(ctname){
          ct = D.span({ className: 'result-contentType'}, '[' + ctname + ']');
        }
      }else if(item.portal_type === 'ExcelFile'){
        ct = D.span({ className: 'result-contentType'}, '[Spreadsheet]');
      }
      var download = '';
      if(DownloadableContentTypes.indexOf(item.portal_type) !== -1){
        var url = item.base_url;
        if(url.substring(url.length - 5) === 'view'){
          url = url.substring(0, url.length - 5);
        }
        if(item.portal_type === 'ExcelFile'){
          url += '/output.xls';
        }
        download = D.span({ className: 'result-download' }, [
          '[',
          D.a({ href: url, target: '_blank'}, 'Download'),
          ']'
        ]);
      }
      var target = '_self';
      if(item.searchSite){
        target = '_blank';
      }

      var modified = moment(item.modified);
      var effective = moment(item.effective);
      var dateNode = '';
      if(effective.isValid()){
        dateNode = D.span({ className: 'result-modified' }, 'Published: ' + effective.format('MMM Do YYYY'));
      } else if(modified.isValid()){
        dateNode = D.span({ className: 'result-modified' }, 'Last modified ' + modified.fromNow());
      }
      return D.li({}, [
        D.span({ className: "result-title" }, [
          ct,
          D.a({ href: item.url, target: target, className: "state-" + item.review_state }, item.Title)
        ]),
        D.span({ className: 'result-url'}, item.base_url),
        dateNode,
        D.span({ className: "result-description" }, item.Description || item.Title),
        download
      ]);
    }
  });

  var SearchOption = R.createClass({
    getDefaultProps() {
      return {
        show: false,
        parent: null,
        type: null,
        options: [],
        label: null,
        labelPrefix: null,
        value: '',
        onClick: function(){}
      }
    },

    render() {
      var that = this;
      var additional = '';
      if(that.props.show === that.props.type){
        var items = that.props.options.map(function(item){
          return D.li({}, D.a({ href: '#', onClick: function(e){
            e.preventDefault();
            that.props.parent.setState({
              show: null
            });
            that.props.onClick(item[0])
          }}, item[1]));
        });
        additional = D.ul({
          className: 'search-additional-sites-listing search-menu-dropdown'}, items);
      }
      var label = that.props.label;
      if (label == null) {
        for(var i=0; i<that.props.options.length; i++) {
          if (that.props.options[i][0] == that.props.value) {
            label = that.props.labelPrefix + that.props.options[i][1];
            break;
          }
        }
      }
      return D.li({
          className: 'search-additional-sites search-menu-dropdown-container' }, [
        D.a({ href: '#',
              className: 'search-additional-sites-btn more-btn',
              onClick: function(e){
          e.preventDefault();
          e.stopPropagation();
          that.props.parent.setState({
            show: that.props.parent.state.show === that.props.type ? null : that.props.type
          });
        }}, label),
        additional
      ]);
    }
  });

  var SearchComponent = R.createClass({

    getInitialState: function(){
      return {
        SearchableText: this.props.SearchableText,
        error: false,
        results: [],
        count: 0,
        pageSize: 20,
        page: this.props.page || 1,
        suggestions: [],
        searchType: this.props.searchType || 'all',
        show: null,
        searchSite: this.props.searchSite || false,
        loading: false,
        sort_on: ''
      };
    },

    getDefaultProps: function(){
      return {
        SearchableText: '',
        searchType: 'all',
        page: 1,
        searchUrl: $('body').attr('data-portal-url') + '/@@searchajax',
        searchTypes: [],
        additionalSites: [],
        searchSite: false
      };
    },

    getSearchType: function(typeId){
      for(var i=0; i<this.props.searchTypes.length; i++){
        var type = this.props.searchTypes[i];
        if(type.id === typeId){
          return type;
        }
      }
    },

    componentDidMount: function(){
      this.load();
    },

    load: function(){
      var that = this;
      that.setState({
        loading: true
      });
      utils.loading.show();
      var state = {
        SearchableText: that.state.SearchableText,
        pageSize: that.state.pageSize,
        page: that.state.page,
        sort_on: that.state.sort_on,
        sort_order: 'descending',
        after: that.state.date || ''
      };
      if(that.state.searchType !== 'all'){
        var type = that.getSearchType(that.state.searchType);
        state = cutils.extend(state, type.query);
        state.searchType = that.state.searchType;
      }
      if(that.state.searchSite){
        state.searchSite = that.state.searchSite;
      }
      if(that.props.Subject){
        state.Subject = that.props.Subject;
      }
      if(that.props['Subject:list']){
        state['Subject:list'] = that.props['Subject:list'];
      }
      if(that.props['path']){
        state['path'] = that.props['path'];
      }
      $.ajax({
        url: this.props.searchUrl,
        data: state
      }).done(function(data){
        that.props.Subject = undefined;
        that.props['Subject:list'] = undefined;
        that.setState({
          results: data.results,
          count: data.count,
          page: data.page,
          error: false,
          suggestions: data.suggestions || [],
          loading: false
        }, function(){
          $('html, body').animate({
            scrollTop: 0
          }, 100);
        });

        if(HasHistory){
          history.pushState(state, "", window.location.origin + window.location.pathname + '?' + $.param(state));
        }
        if(window.ga){
          window.ga('send', 'pageview');
        }
        if(window._paq){
          window._paq.push([
            'trackSiteSearch',
            that.state.SearchableText,
            false,
            data.count
          ]);
          window._paq.push(['trackPageView']);
        }
      }).fail(function(){
        that.setState({
          error: true
        });
      }).always(function(){
        utils.loading.hide();
        that.setState({
          loading: false
        });
      });
    },

    searchClicked: function(e){
      e.preventDefault();
      this.load();
    },

    textChanged: function(e){
      var that = this;
      that.setState({
        SearchableText: e.target.value,
        page: 1
      });
      if(that._timeout){
        clearTimeout(that._timeout);
      }
      that._timeout = setTimeout(function(){
        that.load();
      }, 400);
    },

    nextPage: function(e){
      var that = this;
      e.preventDefault();
      this.setState({
        page: this.state.page + 1
      }, function(){
        that.load();
      });
    },

    prevPage: function(e){
      var that = this;
      e.preventDefault();
      this.setState({
        page: this.state.page - 1
      }, function(){
        that.load();
      });
    },

    renderPaging: function(){
      var that = this;
      if(that.state.count <= that.state.results.length){
        return D.div({});
      }

      var prev = '';
      if(that.state.page > 1){
        prev = D.a({ href: "#", className: "page prev", onClick: that.prevPage}, [
          'Previous'
        ]);
      }
      var next = '';
      var start = (that.state.page - 1) * that.state.pageSize;
      var end = start + that.state.results.length;
      if(end < that.state.count){
        next = D.a({ href: "#", className: "page next", onClick: that.nextPage}, [
          'Next'
        ]);
      }
      return D.p({ className: "bottom-total" }, [
        prev,
        next
      ]);
    },

    renderResults: function(){
      var that = this;
      if(that.state.count === 0){
        if (that.state.loading) {
          return D.div({ className: 'search-empty-results'}, D.p({}, 'Searching…'));
        } else {
          return D.div({ className: 'search-empty-results'}, D.p({}, 'No results found'));
        }
      }
      var results = [];
      that.state.results.forEach(function(item){
        item.searchSite = that.state.searchSite;
        results.push(R.createElement(SearchResult, item));
      });
      return D.div({ id: "search-results-wrapper" }, [
        D.div({ id: "search-results-bar" }, [
          D.span({ id: "results-count" }, [
            'Page ',
            that.state.page,
            ' of ',
            that.state.count,
            ' results'
          ])
        ]),
        D.div({ id: "search-results" }, [
          D.ul({ className: "searchResults" }, results),
          this.renderPaging()
        ])
      ]);
    },

    renderSuggestions: function(){
      var that = this;
      if(that.state.suggestions.length === 0){
        return D.div({});
      }
      var suggestions = [D.li({ className: 'label'}, 'Search instead for: ')];
      that.state.suggestions.forEach(function(suggestion){
        suggestions.push(D.li({ className: 'suggestion'}, [
          D.a({ href: '#', onClick: function(e){
            e.preventDefault();
            that.setState({
              SearchableText: suggestion.text
            }, function(){
              that.load();
            });
          }}, suggestion.text)
        ]));
      });
      return D.div({ className: 'search-suggestions' }, [
        D.ul({ className: 'inline-list' }, suggestions)
      ]);
    },

    renderSeachType: function(type){
      var that = this;
      return D.li({className: that.state.searchType === type.id && 'searchType active' || 'searchType'},
        D.a({ href: '#', onClick: function(e){
          e.preventDefault();
          that.setState({
            searchType: type.id,
            show: null,
            page: 1
          }, function(){
            that.load();
          });
        }}, type.label));
    },

    renderSearchOptions: function(){
      var that = this;
      var options = [D.li({ className: that.state.searchType === 'all' && 'active' || ''},
        D.a({href: '#', onClick: function(e){
          e.preventDefault();
          that.state.searchType = 'all';
          that.load();
        }}, 'All'))];

      if(!that.state.searchSite){
        that.props.searchTypes.slice(0, 3).forEach(function(option){
          options.push(that.renderSeachType(option));
        });
        if(that.props.searchTypes.length > 3){
          var more = '', className = 'search-type-more search-menu-dropdown-container';
          that.props.searchTypes.slice(3).forEach(function(option){
            if(option.id === that.state.searchType){
              options.push(that.renderSeachType(option));
            }
          });
          if(that.state.show === 'more'){
            var moreTypes = [];
            that.props.searchTypes.slice(3).forEach(function(option){
              if(option.id !== that.state.searchType){
                moreTypes.push(that.renderSeachType(option, true));
              }
            });
            more = D.ul({ className: 'search-menu-dropdown'}, moreTypes);
            className += ' showing';
          }
          options.push(D.li({ className: className }, [
            D.a({ href: '#', className: 'more-btn', onClick: function(e){
              e.preventDefault();
              e.stopPropagation();
              that.setState({
                show: that.state.show === 'more' ? null : 'more'
              });
            }}, 'More'),
            more
          ]));
        }
      }

      if(that.props.additionalSites.length > 0){
        var current = this.props.currentSiteLabel || 'current site'
        var items = [['', current]].concat(that.props.additionalSites.map(function(v){
          return [v, v];
        }));
        options.push(R.createElement(SearchOption, {
          show: that.state.show,
          type: 'additionalSites',
          options: items,
          parent: that,
          labelPrefix: 'Search: ',
          value: that.state.searchSite,
          onClick: function(val) {
            var searchType = that.state.searchType;
            var searchSite = false;
            if (val === current) {
              searchType = 'all';
            } else {
              searchSite = val
            }
            that.setState({
              searchSite: searchSite,
              page: 1,
              searchType: searchType
            }, function(){
              that.load();
            });
          }
        }));
      }
      options.push(R.createElement(SearchOption, {
        show: that.state.show,
        type: 'publication',
        parent: that,
        options: SortOptions,
        labelPrefix: 'Sort: ',
        value: that.state.sort_on,
        onClick: function(val) {
          that.setState({
            sort_on: val
          }, function(){
            that.load();
          });
        }
      }));
      options.push(R.createElement(SearchOption, {
        show: that.state.show,
        type: 'date',
        parent: that,
        value: that.state.date,
        options: [
          ['', 'Any Time'],
          [moment().subtract(1, 'days').format('YYYY-MM-DD'), 'Yesterday'],
          [moment().subtract(2, 'days').format('YYYY-MM-DD'), 'Last 2 Days'],
          [moment().subtract(7, 'days').format('YYYY-MM-DD'), 'Last Week'],
          [moment().subtract(30, 'days').format('YYYY-MM-DD'), 'Last Month'],
          [moment().subtract(60, 'days').format('YYYY-MM-DD'), 'Last 2 Months'],
          [moment().subtract(365, 'days').format('YYYY-MM-DD'), 'Last Year'],
        ],
        labelPrefix: 'When: ',
        onClick: function(val) {
          var sort_on = that.state.sort_on;
          if (!sort_on) {
            sort_on = 'effective';
          }
          that.setState({
            date: val,
            sort_on: sort_on
          }, function(){
            that.load();
          });
        }
      }));

      return D.div({ className: 'search-options'}, [
        D.ul({}, options)
      ]);
    },

    render: function(){
      return D.form({ id: "searchform", actionName: "@@search", role: "search",
                      className: "search-form" }, [
        D.div({ className: "search-input-group" }, [
          D.input({ className: "search-input", name: "SearchableText",
                    type: "text", size: "25", title: "Search Site",
                    onChange: this.textChanged, value: this.state.SearchableText,
                    ref: 'searchInput'}),
          D.input({ className: "search-btn",
                    type: "submit", value: "Search",
                    onClick: this.searchClicked }),
          D.div({ className: "visualClear" }, ' ')
        ]),
        this.renderSearchOptions(),
        this.renderSuggestions(),
        this.renderResults()
      ]);
    }
  });

  var page = 1, searchType = 'all', Subject, Subjectlist, path;
  var searchSite = false;
  try{
    page = parseInt(getParameterByName('page'));
  }catch(e){}
  try{
    searchType = getParameterByName('searchType');
  }catch(e){}
  try{
    Subject = getParameterByName('Subject');
  }catch(e){}
  try{
    Subjectlist = getParameterByName(encodeURIComponent('Subject:list'));
  }catch(e){}
  try{
    path = getParameterByName('path');
  }catch(e){}

  try{
    searchSite = getParameterByName('searchSite');
  }catch(e){}

  var el = document.getElementById('searchComponent');
  var component = R.render(R.createElement(
    SearchComponent, cutils.extend(JSON.parse(el.getAttribute('data-search')), {
      SearchableText: getParameterByName('SearchableText') || '',
      Subject: Subject,
      'Subject:list': Subjectlist,
      searchUrl: el.getAttribute('data-search-url'),
      searchType: searchType,
      page: page,
      searchSite: searchSite,
      path: path
    })), el);

  window.onpopstate = function(e){
    if(e.state){
      component.setState(e.state);
      component.load();
    }
  };

  $(window).on('click', function(){
    component.setState({
      show: null
    });
  });

});
