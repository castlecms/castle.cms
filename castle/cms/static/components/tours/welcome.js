

define([
  'jquery'
], function($){
  'use strict';

  var steps = [{
      intro: "Welcome to CastleCMS. We've created a guide to help you get acquainted."
    }, {
      element: document.querySelector('.castle-toolbar-container-side'),
      intro: 'The toolbar lets you make all content changes.',
      position: 'right'
    }, {
      element: document.querySelector('.castle-toolbar-folder_contents'),
      intro: 'Use the Contents button to view your site \'s structure, organize content, and make batch edits.',
      position: 'right'
    }, {
      element: document.querySelector('.castle-toolbar-edit'),
      intro: 'Click the Edit button to edit the current page or change its properties and settings.',
      position: 'right',
      valid: function(){
        return $('.castle-toolbar-edit').length > 0;
      }
    }, {
      element: document.querySelector('.castle-toolbar-add'),
      intro: 'Use the Add button to add content, whether a page, folder, news item, or more.',
      position: 'right',
      valid: function(){
        return $('.castle-toolbar-add').length > 0;
      }
    }, {
      element: document.querySelector('.castle-toolbar-slots'),
      intro: 'Use the Slots button to add content above, below or on the sides of the main content area. ' +
             "The number and location of slots available depends on the site's theme.",
      position: 'right',
      valid: function(){
        return $('.castle-toolbar-slots').length > 0;
      }
    }, {
      element: document.querySelector('.castle-btn-dropdown-user'),
      intro: 'The user menu contains user-specific functions such as viewing your dashboard, ' +
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
