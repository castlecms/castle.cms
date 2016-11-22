

define([
  'jquery'
], function($){

  return function(){

    var initialSteps = [{
      element: document.querySelector('#add-modal-react-container .select-type'),
      intro: "The type of content you are allowed to add to this section of the site is listed here."
    }, {
      element: document.querySelector('#add-modal-react-container'),
      intro: "To upload files, images, videos or mp3s, use the upload button."
    }];

    var addSteps = [{
      element: document.querySelector('#contentTitle'),
      intro: "A title is always required for your content."
    }, {
      element: document.querySelector('#contentId'),
      intro: "The ID is used to construct the content url."
    }, {
      element: document.querySelector('#contentLocation'),
      intro: "Content is Castle is organized as folders. Urls are generated from the " +
             "folder structure you organize your content around. You can manually type " +
             "a folder structure and Castle will automatically generate the missing folders."
    }, {
      element: document.querySelector('#add-modal-react-container .contenttype-folder'),
      intro: "Or you can click the folder icon to explore folders on the site to find where " +
             "your content should be placed."
    }, {
      element: document.querySelector('#add-modal-react-container #contentState'),
      intro: "Select if your content should be private or published immediately."
    }, {
      element: document.querySelector('#after-add-content-radio'),
      intro: "By selecting \"Add another,\" you can immediately create additional content " +
             "instead of immediately editing the content you create."
    }];

    return [{
      name: 'addcontentinitial',
      steps: initialSteps,
      after: function(_initialize){
        $('#add-modal-react-container .select-type a').on('click', function(){
          setTimeout(function(){
            _initialize();
          }, 200);
        });
      },
      show: function(){
        return $('#add-modal-react-container').length > 0;
      }
    }, {
      name: 'addcontentadd',
      steps: addSteps,
      show: function(){
        return $('#add-modal-react-container #contentTitle:visible').length > 0;
      }
    }];
  };
});
