/* global history */


require([
  'jquery',
  'castle-url/libs/react/react.min',
  'castle-url/components/search-component',
  'mockup-utils',
  'castle-url/components/utils',
  'moment'
], function($, R, SearchComponent, utils, cutils, moment){
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

  var page = 1, searchType = 'all', Subject;
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
    searchSite = getParameterByName('searchSite');
  }catch(e){}

  var el = document.getElementById('searchComponent');
  var component = R.render(R.createElement(SearchComponent, cutils.extend(JSON.parse(el.getAttribute('data-search')), {
    SearchableText: getParameterByName('SearchableText') || '',
    Subject: Subject,
    searchUrl: el.getAttribute('data-search-url'),
    searchType: searchType,
    page: page,
    searchSite: searchSite
  })), el);

  window.onpopstate = function(e){
    if(e.state){
      component.setState(e.state);
      component.load();
    }
  };

  $(window).on('click', function(){
    if(component.state.showMore){
      component.setState({
        showMore: false
      });
    }
    if(component.state.showAdditionalSites){
      component.setState({
        showAdditionalSites: false
      });
    }
  });

});
