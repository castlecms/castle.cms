/* global window */

define([
  'jquery',
  'mockup-utils',
  'castle-url/libs/react/react.min',
  'castle-url/components/utils',
  'castle-url/components/modal'
], function($, utils, R, cutils, Modal){
  'use strict';

  var D = R.DOM;

  var ConfirmationModalComponent = cutils.Class([Modal], { // jshint ignore:line
    getInitialState: function(){
      return {
        finished: this.props.finished,
        disabled: false
      };
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'confirmation-modal',
        title: 'Confirm user action',
        msg: 'Are you certain you want to do this?',
        successMsg: 'You have successfully completed this action.',
        confirmBtnLabel: 'Yes',
        cancelBtnLabel: 'No',
        finishHideDelay: 1200,
        finished: false,
        onConfirm: function(cmp){
          cmp.setState({
            finished: true
          });
        },
        onCancel: function(cmp){
          cmp.hide();
        }
      });
    },

    finishWithSuccess: function(){
      // show success and then close after a bit
      var that = this;
      that.setState({
        finished: true
      }, function(){
        setTimeout(function(){
          that.hide();
        }, that.props.finishHideDelay);
      });
    },

    renderContent: function(){
      var warning = '';
      var success = '';
      if(!this.state.finished){
        warning = D.div({className: "portalMessage warning"}, [
          D.strong({}, 'Warning'), this.props.msg]);
      }else{
        success = D.div({className: "portalMessage info"}, [
          D.strong({}, 'Success'), this.props.successMsg]);
      }
      return D.div({ className: 'castle-reset-password'}, [
        warning,
        success
      ]);
    },
    renderFooter: function(){
      var that = this;
      var buttons = [];
      if(!that.state.finished && !that.state.disabled){
        buttons.push(D.button({ className: 'plone-btn plone-btn-default',
                                onClick: this.hide }, that.props.cancelBtnLabel));
        buttons.push(D.button({ className: 'plone-btn plone-btn-danger',
                                onClick: function(){
                                  that.props.onConfirm(that);
                                }}, that.props.confirmBtnLabel));
      }
      return D.div({}, buttons);
    }
  });

  return ConfirmationModalComponent;
});
