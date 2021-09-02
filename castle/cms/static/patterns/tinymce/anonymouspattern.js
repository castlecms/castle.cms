/* global tinymce, jQuery */

(function($) { $(function() {
    // manually load tinymce is user is not authenticated...
    if($('body.userrole-authenticated').size() === 0){
      require(['tinymce'], function(){
        $('.pat-textareamimetypeselector').each(function(){
          var $tinymce = $(this).prev();
          // hide the textareamimetypeselector
          $(this).hide();

          var id = 1 + Math.floor(100000 * Math.random());
          $tinymce.attr('id', id);
          tinymce.init({
            selector: "#" + id
          });
        });
      });
    }

}); })(jQuery);
