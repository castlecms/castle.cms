/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'castle-url/libs/react/react',
  'castle-url/components/snackbar'
], function($, Base, R, Snackbar) {
  'use strict';
  var D = R.DOM;

  var SubscribersComponent = R.createClass({
    getDefaultProps: function() {
      return {
        portalUrl: $('body').attr('data-portal-url'),
        data: JSON.parse($('.pat-subscribers').attr('data-pat-manage-subscribers'))
      }
    },
    getInitialState: function() {
      var page = this.props.data['page'];
      var subscriberCount = this.props.data['subscriberCount'];
      return {
        page: page,
        perPage: 1,
        subscriberCount: subscriberCount,
        subscribers: []
      };
    },
    componentDidMount: function() {
      this.getPage(1);
    },
    render: function(){
      var content = [
        D.div({
          id: "snackbar"
        }, 'User Deleted!'),
        this.renderResults()
      ];
      var snackbar = document.getElementById("snackbar");
      if (snackbar) {
        this.state.snackbar = R.render(R.createElement(Snackbar),snackbar);
      }
      if (this.state.subscriberCount > this.state.perPage) {
          content.push(this.renderPaging());
      }
      return D.div({ className: 'castle-manage-subscribers'}, content);
    },
    renderResults: function(){
      if (this.state.subscribers) {
        var results = [];
        for (var i=0;i<this.state.subscribers.length;i++){
          results.push(
            D.div({
              className: 'castle-subscriber'
            }, [
                this.state.subscribers[i].email,
                D.a({
                  onClick: this.deleteSubscriber,
                  target: i
                }, 'Delete')
               ])
          )
        }
        return results;
      }
    },
    renderPaging: function(){
      var pages = [];
      var that = this;
      var pageCount = Math.ceil(this.state.subscriberCount / this.state.perPage);
      var pageClick = function(event) {
        event.preventDefault();
        var page = parseInt(event.target.target)
        if (page > 0 && page <= pageCount){
          var subscribers = that.getPage(page);
          that.setState({
            page: page,
            subscribers: subscribers
          });
        }
      }
      var renderPage = function(number, label) {
        var liAttributes = {
          className: 'page-item'
        }
        if (label == undefined) {
          label = number;
        }
        if (number == that.state.page) {
          liAttributes.className = 'page-item current';
        } else if (number < 1 || number > pageCount) {
          liAttributes.className = 'page-item disabled'
        }
        var link = D.a({
          onClick: pageClick,
          href: number,
          target: number,
          className: 'page-link'
        }, label)
        var page = D.li(liAttributes, link);
        return page;
      }
      pages.push(renderPage(1, 'First'));
      pages.push(renderPage(this.state.page-1, 'Prev'));
      if (this.state.page > 1 ) {
        if (this.state.page > 2) {
          pages.push(renderPage(this.state.page-2));
        }
        pages.push(renderPage(this.state.page-1));
      }
      pages.push(renderPage(this.state.page));
      var nextPage = this.state.page+1;
      while (pages.length < 10 && nextPage<=pageCount) {
        pages.push(renderPage(nextPage));
        nextPage++;
      }
      pages.push(renderPage(this.state.page+1, 'Next'));
      pages.push(renderPage(pageCount, 'Last'));
      return D.div({
        className: 'paging'
      }, D.ul({
          className: 'pagination'
        }, pages));
    },
    getPage: function(pageNum){
      var that = this;
      var url = this.props.portalUrl + '/manage-subscribers?page=' + pageNum;
      $.ajax({
        url: url,
        success: function(results){
          that.setState({
            subscribers: results,
            page: pageNum
          })
        },
        error: function(){
          //handle error
        }
      });
    },
    deleteSubscriber: function(){
      event.preventDefault();

      var subscriberIndex = parseInt(event.target.target);
      var that = this;
      var url = this.props.portaUrl + '/manage-subscribers?action=delete&email=' + subscriberIndex
      $.ajax({
        url: url,
        success: function(result){
          that.state.snackbar.showText('User Deleted!');
          that.getPage(that.state.page);
        },
        error: function(){
          //handle error
        }
      });
    }
  });

  var ManageSubscribers = Base.extend({
    name: 'manage-subscribers',
    trigger: '.pat-subscribers',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var that = this;
      var component = R.render(R.createElement(SubscribersComponent, that.options), that.$el[0], function(){
        if(document.body.className.indexOf('subscribers-initialized') === -1){
          document.body.className += ' subscribers-initialized';
        }
        $('body').trigger('subscribers-initialized', that, component);
      });
    },
  });

  return ManageSubscribers;

});
