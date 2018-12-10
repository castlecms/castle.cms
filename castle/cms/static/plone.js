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
  'pat-registry',
  'pat-base',
  'mockup-patterns-modal',
  'mockup-patterns-select2',
  'mockup-patterns-pickadate',
  'mockup-patterns-autotoc',
  'mockup-patterns-cookietrigger',
  'mockup-patterns-formunloadalert',
  'mockup-patterns-preventdoublesubmit',
  'mockup-patterns-formautofocus',
  'mockup-patterns-markspeciallinks',
  'bootstrap-dropdown',
  'bootstrap-collapse',
  'bootstrap-tooltip',
  'castle-url/patterns/slider',
  'castle-url/patterns/gallery',
  'castle-url/patterns/map',
  'castle-url/patterns/queryfilter',
  'castle-url/patterns/audio',
  'castle-url/patterns/video',
  'castle-url/patterns/fullcalendar',
  'castle-url/patterns/subscribe',
  'castle-url/patterns/facebook',
  'castle-url/patterns/focuspoint',
  'castle-url/patterns/masonry',
  'castle-url/patterns/existing',
  'castle-url/patterns/survey',
  'castle-url/patterns/modallink',
], function($, registry, Base, Modal) {
  'use strict';

  Modal.prototype.defaults.actionOptions.timeout = 10000;

  // initialize only if we are in top frame
  $(document).ready(function() {
    $('body').addClass('pat-plone');
    if (!registry.initialized) {
      registry.init();
    }
  });

$(document).ready(function(){

  /* add close buttons to portalMessage */
  $('.portalMessage').each(function(){
    var $el = $(this);
    var $btn = $('<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>');
    $el.prepend($btn);
    $btn.on('click', function(e){
      e.preventDefault();
      $el.fadeOut();
    });
  });


  /* feature tile integration,
     this could be a pattern. will just leave here for now... */
  var $features = $('.feature-tile-container');
  $features.each(function(){
    var $feature = $(this);
    var $details = $('.feature-tile-expanded-container', $feature);

    var $rowContainer = $feature.closest('.row .mosaic-grid-cell');

    $rowContainer.addClass('feature-tile-row');
    $details.insertAfter($rowContainer);

    $('.feature-tile-item', $feature).on('click', function(){
      var enabled = false;
      if($feature.hasClass('active')){
        enabled = true;
      }
      $features.removeClass('active');
      $('.feature-tile-expanded-container').removeClass('active');

      if(!enabled){
        // should be able to close
        $details.addClass('active');
        $feature.addClass('active');
      }
    });
  });

});


});
