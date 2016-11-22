

define([
  'jquery'
], function($){
  return {
    selectFieldset: function(name){
      var id = 'fieldset-' + name;
      var $fieldset = $('#' + id);
      var $form = $fieldset.parents('form');
      var $tab = $('.autotoc-nav a', $form).eq($fieldset.index() - 1).addClass('active');
      $('fieldset', $form).removeClass('active');
      $('.autotoc-nav a', $form).removeClass('active');
      $tab.addClass('active');
      $fieldset.addClass('active');
    }
  };
});
