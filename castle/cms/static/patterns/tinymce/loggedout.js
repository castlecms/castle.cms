/* global tinymce, jQuery */

(function($) { $(function() {
    require(['mockup-patterns-tinymce']);

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
            name: 'tinymce',
            trigger: '.pat-tinymce',
            parser: 'mockup',
            defaults: {
                relatedItems: {
                    // UID attribute is required here since we're working with related items
                    attributes: ['UID', 'Title', 'portal_type', 'path','getURL', 'getIcon','is_folderish','review_state'],
                    batchSize: 20,
                    vocabularyUrl: null,
                    width: 500,
                    maximumSelectionSize: 1,
                    // placeholder: _t('Search for item on site...')
                },
                text: {
                    insertBtn: ('Insert'), // so this can be configurable for different languages
                    cancelBtn: ('Cancel'),
                    insertHeading: ('Insert link'),
                    title: ('Title'),
                    internal: ('Internal'),
                    external: ('External URL (can be relative within this site or absolute if it starts with http:// or https://)'),
                    email: ('Email Address'),
                    anchor: ('Anchor'),
                    subject: ('Email Subject (optional)'),
                    image: ('Image'),
                    imageAlign: ('Align'),
                    scale: ('Size'),
                    alt: ('Alternative Text'),
                    externalImage: ('External Image URL (can be relative within this site or absolute if it starts with http:// or https://)')
                },
                // URL generation options
                loadingBaseUrl: '../../../bower_components/tinymce-builded/js/tinymce/',
                prependToUrl: '',
                appendToUrl: '',
                linkAttribute: 'path', // attribute to get link value from data
                prependToScalePart: '/imagescale/', // some value here is required to be able to parse scales back
                appendToScalePart: '',
                appendToOriginalScalePart: '',
                defaultScale: 'large',
                scales: ('Listing (16x16):listing,Icon (32x32):icon,Tile (64x64):tile,' +
                        'Thumb (128x128):thumb,Mini (200x200):mini,Preview (400x400):preview,' +
                        'Large (768x768):large'),
                targetList: [
                    {text: ('Open in this window / frame'), value: ''},
                    {text: ('Open in new window'), value: '_blank'},
                    {text: ('Open in parent window / frame'), value: '_parent'},
                    {text: ('Open in top frame (replaces all frames)'), value: '_top'}
                ],
                imageTypes: ['Image'],
                folderTypes: ['Folder', 'Plone Site'],
                tiny: {
                    'content_css': '../../../bower_components/tinymce-builded/js/tinymce/skins/lightgray/content.min.css',
                    theme: 'modern',
                    plugins: ['advlist', 'autolink', 'lists', 'charmap', 'print', 'preview', 'anchor', 'searchreplace',
                            'visualblocks', 'code', 'fullscreen', 'insertdatetime', 'media', 'table', 'contextmenu',
                            'paste', 'plonelink', 'ploneimage'],
                    menubar: 'edit table format tools view insert',
                    toolbar: 'undo redo | styleselect | bold italic | ' +
                            'alignleft aligncenter alignright alignjustify | ' +
                            'bullist numlist outdent indent | ' +
                            'unlink plonelink ploneimage',
                    //'autoresize_max_height': 900,
                    'height': 400,
                    // stick here because it's easier to config without
                    // additional settings
                    linkTypes: ['internal', 'external', 'email', 'anchor']
                },
                inline: false
            }});
        });
      });
    }

}); })(jQuery);