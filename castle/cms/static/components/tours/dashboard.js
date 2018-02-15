

define([
  'jquery'
], function($){
  var steps = [{
      intro: "You are now viewing the dashboard. You will be brought here every time after you login"
    }, {
      element: document.querySelector('.dashboard-add-content-buttons'),
      intro: 'These buttons are dynamically generated depending on what actions you ' +
             'perform on the site most often.',
      position: 'bottom'
    }, {
      element: document.querySelector('.recent-activity'),
      intro: 'Will give you an up-to-date list of the most recent site activity.',
      position: 'top'
    }];

  return {
    name: 'dashboard',
    before: function(){
    },
    after: function(){
    },
    steps: steps,
    show: function(){
      return $('body').hasClass('template-dashboard');
    }
  };
});
