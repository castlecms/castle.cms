

define([
  'jquery'
], function($){
  'use strict';

  var steps = [{
      intro: "Welcome to Castle CMS. We've created a guide to help you get acquainted."
    }, {
      element: document.querySelector('.castle-toolbar-container-side'),
      intro: 'The toolbar is where you will initiate all CMS changes.',
      position: 'right'
    }, {
      element: document.querySelector('.castle-toolbar-manage-content'),
      intro: 'To view site structure, batch edit and organize content, use the Contents menu.',
      position: 'right'
    }, {
      element: document.querySelector('.castle-toolbar-edit'),
      intro: 'Click the edit button to edit the current page you are viewing',
      position: 'right',
      valid: function(){
        return $('.castle-toolbar-edit').length > 0;
      }
    }, {
      element: document.querySelector('.castle-toolbar-add'),
      intro: 'To add a new page to the site, use the "Add new" menu item.',
      position: 'right',
      valid: function(){
        return $('.castle-toolbar-add').length > 0;
      }
    }, {
      element: document.querySelector('.castle-toolbar-slots'),
      intro: 'To add content above, below or on the sides of your content body, use the Slots menu item. ' +
             "The amount of slots available depends on the site's theme.",
      position: 'right',
      valid: function(){
        return $('.castle-toolbar-slots').length > 0;
      }
    }, {
      element: document.querySelector('.castle-btn-dropdown-user'),
      intro: 'The user menu is for user specific functions like going back to your dashboard, ' +
             'changing preferences and logging out.',
      position: 'bottom'
    }];

  return {
    name: 'welcome',
    before: function(){
    },
    after: function(){
    },
    steps: steps
  };
});
