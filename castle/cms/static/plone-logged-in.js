// Copyright (C) 2010 Plone Foundation
//
// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation; either version 2 of the License.
//
// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along with
// this program; if not, write to the Free Software Foundation, Inc., 51
// Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
//

if (window.jQuery) {
  define( 'jquery', [], function () {
    'use strict';
    return window.jQuery;
  } );
}

require([
  'jquery',
  'mockup-patterns-modal',
  'mockup-utils',
  'castle-url/patterns/toolbar',
  'mockup-patterns-relateditems',
  'mockup-patterns-querystring',
  'mockup-patterns-tinymce',
  'mockup-patterns-textareamimetypeselector',
  'mockup-patterns-inlinevalidation',
  'mockup-patterns-structure',
  'mockup-patterns-recurrence',
  'castle-url/patterns/edittile',
  'castle-url/patterns/castledynamicform',
  'castle-url/patterns/mapselect',
  'castle-url/patterns/previewselect',
  'castle-url/patterns/imagewidget',
  'castle-url/patterns/focalpointselect'
], function($, Modal, utils) {
  'use strict';

  /* XXX monkey patch modal to NOT squash all clicks */
  if(Modal.prototype._init === undefined){
    Modal.prototype._init = Modal.prototype.init;
    Modal.prototype.init = function(){
      this.options.loadLinksWithinModal = false;
      this.options.backdropOptions.closeOnClick = false;
      this.options.backdropOptions.closeOnEsc = false;
      Modal.prototype._init.apply(this, []);
    };
  }

  if($(window).width() > 1040){
    $(document).ready(function(){
      if($('body').attr('data-show-tour')){
        require(['castle-url/components/tour'], function(){});
      }
    });
  }

  // TODO: Needs to be moved to controlpanel js
  $(document).ready(function() {
    var cookieNegotiation = (
      $("#form-widgets-use_cookie_negotiation > input").value === 'selected');
    if (cookieNegotiation !== true) {
      $("#formfield-form-widgets-authenticated_users_only").hide();
    }else{
      $("#formfield-form-widgets-authenticated_users_only").show();
    }

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
