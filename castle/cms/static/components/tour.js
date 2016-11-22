/* global define */


define([
  'jquery',
  'underscore',
  'castle-url/libs/intro.js/intro',
  'mockup-utils',
  'castle-url/components/tours/welcome',
  'castle-url/components/tours/dashboard',
  'castle-url/components/tours/foldercontents',
  'castle-url/components/tours/editpage',
  'castle-url/components/tours/addcontent',
  'jquery.cookie'
], function($, _, Intro, utils, WelcomeTour, DashboardTour, FolderContentsTour,
            EditPageTour, AddContentTour) {
  'use strict';

  var availableTours = [
    WelcomeTour,
    DashboardTour,
    FolderContentsTour,
    EditPageTour,
    AddContentTour
  ];

  var alreadyViewed = $('body').attr('data-show-tour');
  if(alreadyViewed){
    alreadyViewed = $.parseJSON(alreadyViewed).viewed;
    if(alreadyViewed.indexOf('all') !== -1){
      return;
    }
  }

var _initialize = function(){
  if(alreadyViewed && alreadyViewed.indexOf('all') !== -1){
    return;
  }

  // find current tour
  var tour = null;

  for(var i=0; i<availableTours.length; i++){
    var _tours = availableTours[i];
    if(typeof(_tours) === "function"){
      _tours = _tours();
    }
    if(_tours.constructor == Object){
      _tours = [_tours];
    }
    var found = false;
    for(var x=0; x<_tours.length; x++){
      var _tour = _tours[x];
      if(alreadyViewed.indexOf(_tour.name) === -1){
        if(_tour.show && !_tour.show()){
          continue;
        }
        tour = _tour;
        found = true
        break;
      }
    }
    if(found){
      break;
    }
  }

  if(tour === null){
    // did not find one that we haven't done
    return;
  }

  var intro = Intro();

  var _currentStep = $.cookie(tour.name + 'tour-step');
  if(!_currentStep){
    _currentStep = 0;
  }else{
    _currentStep = parseInt(_currentStep) || 0;
  }
  var _currentEl = null;

  intro.setOptions({
    showProgress: true,
    scrollToElement: true,
    disableInteraction: true,
    overlayOpacity:0.1,
    steps: tour.steps
  });

  intro.onbeforechange(function(el){
    var prevStep = tour.steps[_currentStep];
    var prevEl = _currentEl;

    if(prevStep && prevStep.onHide){
      prevStep.onHide(prevEl, el, prevStep);
    }

    _currentStep = intro._currentStep;
    $.cookie(tour.name + 'tour-step', _currentStep);
    _currentEl = el;

    var nextStep = tour.steps[_currentStep];
    if(nextStep && nextStep.onShow){
      nextStep.onShow(prevEl, el, nextStep);
    }
  });

  intro.onchange(function(el){
  });

  intro.onafterchange(function(el){

    var nextStep = tour.steps[_currentStep];
    if(nextStep.valid && !nextStep.valid()){
      if(intro._direction === 'forward'){
        intro.goToStep(_currentStep + 2);
      }else{
        intro.goToStep(_currentStep);
      }
    }

    // add in skip all tours button
    $('.introjs-skipall').remove();
    var $skipAll = $('<a class="introjs-button introjs-skipall" href="javascript:void(0);">Skip all</a>');
    $('.introjs-tooltipbuttons').prepend($skipAll);
    $skipAll.on('click', function(e){
      e.preventDefault();
      intro.exit();
      alreadyViewed.push('all');
      $.ajax({
        url: $('body').attr('data-portal-url') + '/@@finished-tour',
        data: {
          _authenticator: utils.getAuthenticator(),
          tour: 'all'
        }
      }).done(function(data){
        if(!data.success){
          // handle error response?
        }
      });
    })
  });

  var _onDone = function(){
    if(tour.after){
      tour.after(_initialize);
    }
    $.cookie(tour.name + 'tour-step', 0);
    $('body').removeClass('tour-active');

    $.ajax({
      url: $('body').attr('data-portal-url') + '/@@finished-tour',
      data: {
        _authenticator: utils.getAuthenticator(),
        tour: tour.name
      }
    }).done(function(data){
      if(!data.success){
        // handle error response?
      }
    });

    alreadyViewed.push(tour.name);
    _initialize();
  };

  intro.onexit(_onDone);
  intro.oncomplete(_onDone);

  if(tour.before){
    tour.before();
  }
  $('body').addClass('tour-active');
  setTimeout(function(){
    intro.start();
  }, 200);

};
_initialize();


  $('#plone-contentmenu-factories > a').on('click', function(){
    _initialize();
  });

});
