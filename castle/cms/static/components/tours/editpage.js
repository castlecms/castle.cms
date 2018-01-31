

define([
  'jquery',
  'castle-url/components/tours/utils'
], function($, utils){
  var steps = [{
      intro: "CastleCMS provides an interactive content editor. " +
             "To edit content, click to select it and just start writing."
    }, {
      element: document.querySelector('.mosaic-button-properties'),
      intro: 'All content has additional properties you can customize: ' +
             'lead images, change notes, tags, dates, and other settings.',
      position: 'bottom',
      onHide: function(){
        $.mosaic.overlay.open('all');
      }
    }, {
      element: document.querySelector('#autotoc-item-autotoc-0'),
      intro: 'The default fieldset contains properties you can set on this content item: ' +
             'related items, tags, mapping locations',
      position: 'bottom'
    }, {
      element: document.querySelector('#autotoc-item-autotoc-1'),
      intro: 'Categorization lets you tag content for ' +
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
      intro: '"Related items" is used to make references to other related content. ' +
             'These references are displayed on the page as clickable links.',
      position: 'top',
      valid: function(){
        return $('#fieldset-categorization').length > 0;
      }
    }, {
      element: document.querySelector('.mosaic-overlay form #formfield-form-widgets-IDublinCore-subjects'),
      intro: 'Tags allow you to further organize your content. This is free-form; you can select ' +
             'existing tags other users have already created on the site or you can create new ones.',
      position: 'top',
      valid: function(){
        return $('#fieldset-categorization').length > 0;
      }
    }, {
      element: document.querySelector('.mosaic-overlay form #formfield-form-widgets-ILocation-coordinates'),
      intro: 'By specifying location coordinates for your content, you can display them on ' +
             'map tiles you can include anywhere on your site. Additionally, KML (geographic XML feeds) can be created ' +
             'to provide mapped content for your site.',
      position: 'top',
      valid: function(){
        return $('#fieldset-categorization').length > 0;
      }
    }, {
      element: document.querySelector('#autotoc-item-autotoc-3'),
      intro: 'You can set an effective date for when your content will be published, ' +
             'and an expiry date for when your content should no longer be visible.',
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
