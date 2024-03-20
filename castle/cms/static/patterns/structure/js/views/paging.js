define( [
  'jquery',
  'underscore',
  'backbone',
  'text!castle-url/patterns/structure/templates/paging.xml',
  'translate'
], function ( $, _, Backbone, PagingTemplate, _t ) {
  'use strict';

  var PagingView = Backbone.View.extend( {
    events: {
      'click a.servernext': 'nextResultPage',
      'click a.serverprevious': 'previousResultPage',
      'click a.serverlast': 'gotoLast',
      'click a.page': 'gotoPage',
      'click a.serverfirst': 'gotoFirst',
      'click a.serverpage': 'gotoPage',
      'click .serverhowmany a': 'changeCount'
    },

    tagName: 'aside',
    template: _.template( PagingTemplate ),
    maxPages: 7,
    MAX_BATCH_SIZE: '100000',
    initialize: function ( options ) {
      this.options = options;
      this.app = this.options.app;
      this.collection = this.app.collection;
      this.collection.on( 'reset', this.render, this );
      this.collection.on( 'sync', this.render, this );

      this.$el.appendTo( '#pagination' );
    },

    render: function () {
      var data = this.collection.info();
      data.pages = this.getPages( data );
      var html = this.template( $.extend( {
        _t: _t
      }, data ) );
      this.$el.html( html );
      return this;
    },

    getPages: function ( data ) {
      var totalPages = data.totalPages;
      if ( !totalPages ) {
        return [];
      }
      var currentPage = data.currentPage;
      var left = 1;
      var right = totalPages;
      if ( totalPages > this.maxPages ) {
        left = Math.max( 1, Math.floor( currentPage - ( this.maxPages / 2 ) ) );
        right = Math.min( left + this.maxPages, totalPages );
        if ( ( right - left ) < this.maxPages ) {
          left = left - Math.floor( this.maxPages / 2 );
        }
      }
      var pages = [];
      for ( var i = left; i <= right; i = i + 1 ) {
        pages.push( i );
      }

      /* add before and after */
      if ( pages[ 0 ] > 1 ) {
        if ( pages[ 0 ] > 2 ) {
          pages = [ '...' ].concat( pages );
        }
        pages = [ 1 ].concat( pages );
      }
      if ( pages[ pages.length - 1 ] < ( totalPages - 1 ) ) {
        if ( pages[ pages.length - 2 ] < totalPages - 2 ) {
          pages.push( '...' );
        }
        pages.push( totalPages );
      }
      return pages;
    },
    nextResultPage: function ( e ) {
      e.preventDefault();
      const nextPage = this.collection.information.next;
      const totalPages = this.collection.information.totalPages;
      const currentPage = this.collection.information.currentPage;
      if (
        nextPage &&
        currentPage &&
        totalPages &&
        nextPage > currentPage &&
        nextPage <= totalPages
      ) {
        this.collection.requestNextPage();
      }
    },
    previousResultPage: function ( e ) {
      e.preventDefault();
      const previousPage = this.collection.information.previous;
      const currentPage = this.collection.information.currentPage;
      if (
        previousPage &&
        currentPage &&
        currentPage > previousPage &&
        previousPage >= 1
      ) {
        this.collection.requestPreviousPage();
      }
    },
    gotoFirst: function ( e ) {
      e.preventDefault();
      const currentPage = this.collection.information.currentPage;
      if ( currentPage && currentPage > 1 ) {
        this.collection.goTo( 1 );
      }
    },
    gotoLast: function ( e ) {
      e.preventDefault();
      const currentPage = this.collection.information.currentPage;
      const totalPages = this.collection.information.totalPages;
      if (
        currentPage &&
        totalPages &&
        currentPage < totalPages
      ) {
        this.collection.goTo( totalPages );
      }
    },
    gotoPage: function ( e ) {
      e.preventDefault();
      var page = $( e.target ).text();
      this.collection.goTo( page );
    },
    changeCount: function ( e ) {
      e.preventDefault();
      var text = $( e.target ).text();
      var per = text === 'All' ? this.MAX_BATCH_SIZE : text;
      this.collection.howManyPer( per );
      this.app.setCookieSetting( 'perPage', per );
    },
  } );

  return PagingView;
} );
