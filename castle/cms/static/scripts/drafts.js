//
// Script used to ping draft support while a user is editing so it doesn't get cleaned
//

require([
  'jquery',
  'mockup-utils'
], function($, utils){
  'use strict';

  $(document).ready(function() {
    if($('.template-edit').size() > 0){
      // we are currently editing a mosaic form, ping draft support every 5 minutes
      // to make sure it increments draft edit time so it doesn't get cleaned
      // when a user it working on it
      var pingDraft = function(){
        setTimeout(function(){
          $.ajax({
            url: $('body').attr('data-base-url') + '/@@ping-draft',
            method: 'POST',
            data: {
              _authenticator: utils.getAuthenticator()
            }
          }).done(function(){
            pingDraft();
          });
        }, 1000 * 60 * 5);
      };
      pingDraft();
    }
  });
});
