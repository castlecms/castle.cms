/* global tinymce, jQuery */

(function($) { $(function() {
    // require(['mockup-patterns-tinymce']);

    // manually load tinymce is user is not authenticated...
    if($('body.userrole-authenticated').size() === 0){
      require(['tinymce'], function(){
        $('.pat-textareamimetypeselector').each(function(){
          // when using the textareamimetypeselector pattern, the textarea
          // is the previous element
          var $tinymce = $(this).prev();
          // hide the textareamimetypeselector
          $(this).hide();

          // we need an id for the tinymce instance
          var id = 1 + Math.floor(100000 * Math.random());
          $tinymce.attr('id', id);

          tinymce.init({
            selector: "#" + id
          });
        });
      });
    }

}); })(jQuery);