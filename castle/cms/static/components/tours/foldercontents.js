

define([
  'jquery'
], function($){
  var steps = [{
      intro: "Contents is a great area to manage and organize your site content."
    }, {
      element: document.querySelector('.popover.attribute-columns'),
      intro: 'Use this button to customize the fields that show up in the listing',
      position: 'right',
      onShow: function(){
        if(!$('.popover.attribute-columns').is(':visible')){
          $('#btn-attribute-columns').trigger('click');
        }
      },
      onHide: function(){
        if($('.popover.attribute-columns').is(':visible')){
          $('#btn-attribute-columns').trigger('click');
        }
      }
    }, {
      element: document.querySelector('#btngroup-mainbuttons'),
      intro: 'These actions are used to batch edit and manage content you have selected.',
      position: 'bottom'
    }, {
      element: document.querySelector('#filter'),
      intro: 'You can also dynamically filter contents of the folder',
      position: 'left'
    }];

  return {
    name: 'foldercontents',
    before: function(){
    },
    after: function(){
    },
    steps: steps,
    show: function(){
      return $('body').hasClass('template-folder_contents');
    }
  };
});
