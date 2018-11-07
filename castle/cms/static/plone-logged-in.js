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
  'castle-url/patterns/focalpointselect',
  'castle-url/patterns/upload-update',
  'castle-url/patterns/widgets',

  // scripts
  'castle-url/scripts/patches',
  'castle-url/scripts/drafts',
  'castle-url/scripts/session'
], function($) {
  'use strict';

  if($(window).width() > 1040){
    $(document).ready(function(){
      if($('body').attr('data-show-tour')){
        require(['castle-url/components/tour'], function(){});
      }
    });
  }
});
