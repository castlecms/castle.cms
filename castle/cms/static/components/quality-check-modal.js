/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/modal',
  'castle-quality-check',
  'castle-url/components/utils'
], function($, Base, _, R, utils, Modal, QualityCheck, cutils) {
  'use strict';
  var D = R.DOM;

  var QualityCheckModalComponent = cutils.Class([Modal], {
    renderContent: function(){
      return R.createElement(QualityCheck, {});
    },
    renderFooter: function(){
      var buttons = [D.button({ type: 'button', className: 'plone-btn plone-btn-default pull-right',
                                'data-dismiss': 'modal'}, 'Done')];
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'quality-content-modal',
        title: 'Quality Check'
      });
    }
  });

  return QualityCheckModalComponent;
});
