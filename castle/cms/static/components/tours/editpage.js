

define([
  'jquery',
  'castle-url/components/tours/utils'
], function($, utils){
  var steps = [{
      intro: "Castle provides an interactive site content editor. " +
             "To edit content, click to select it and just start writing."
    }, {
      element: document.querySelector('.mosaic-button-properties'),
      intro: 'Site content has additional properties you will likely want to customize ' +
             'while managing your content.',
      position: 'bottom',
      onHide: function(){
        $.mosaic.overlay.open('all');
      }
    }, {
      element: document.querySelector('#autotoc-item-autotoc-0'),
      intro: 'Default fieldset will have main site properties that are not included on the page.',
      position: 'bottom'
    }, {
      element: document.querySelector('#autotoc-item-autotoc-1'),
      intro: 'Categorization will help you to tag and organize you content for ' +
             'easier management and searching later.',
      position: 'bottom',
      valid: function(){
        return $('#fieldset-categorization').length > 0;
      },
      onShow: function(){
        utils.selectFieldset('categorization');
      }
    }, {
      element: document.querySelector('.mosaic-overlay form #formfield-form-widgets-IRelatedItems-relatedItems'),
      intro: 'Related items is used to make useful references between content. ' +
             'These references can then be utilized to dynamically render related content onto pages ' +
             'or just help you query and organize your content.',
      position: 'top',
      valid: function(){
        return $('#fieldset-categorization').length > 0;
      }
    }, {
      element: document.querySelector('.mosaic-overlay form #formfield-form-widgets-IDublinCore-subjects'),
      intro: 'Tags allow you to further organize your content. This is free-form, you can select ' +
             'existing tags users have entered on the site or write your own new tags.',
      position: 'top',
      valid: function(){
        return $('#fieldset-categorization').length > 0;
      }
    }, {
      element: document.querySelector('.mosaic-overlay form #formfield-form-widgets-ILocation-coordinates'),
      intro: 'By mapping your content, when you include maps on pages, this content will ' +
             'populate map points. Additionally, KML(geographic XML feeds) can be created ' +
             'to provide mapped content for your site.',
      position: 'top',
      valid: function(){
        return $('#fieldset-categorization').length > 0;
      }
    }, {
      element: document.querySelector('#autotoc-item-autotoc-3'),
      intro: 'Use date settings to help sort content listing your content is included in',
      position: 'bottom',
      valid: function(){
        return $('#fieldset-dates').length > 0;
      },
      onShow: function(){
        utils.selectFieldset('dates');
      },
      onHide: function(){
        $.mosaic.overlay.close();
      }
    }, {
      element: document.querySelector('.mosaic-button-group-layout'),
      intro: 'Use the layout button to change, customize or save layouts.',
      position: 'bottom',
    }];

  return {
    name: 'editpage',
    before: function(){
    },
    after: function(){
    },
    steps: steps,
    show: function(){
      return $('body').hasClass('template-layout') && $('body').hasClass('template-edit');
    }
  };
});
