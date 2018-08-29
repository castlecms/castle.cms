/* global window */

require([
  'jquery',
  'pat-registry',
  'mockup-patterns-modal',
  'mockup-utils',
  'castle-url/libs/react/react.min',
  'castle-url/components/utils',
  'castle-url/components/modal',
  'castle-url/components/confirm'
], function($, Registry, PloneModal, utils, R, cutils, Modal,
            ConfirmationModalComponent){
  'use strict';

  var D = R.DOM;

  var rebind = function(data){
    var $body = $(utils.parseBodyTag(data));
    var $content = $('.pat-formautofocus', $body);
    $('.pat-formautofocus').replaceWith($content);
    Registry.scan($('.pat-formautofocus'));
    bind();
  };

  var executeAction = function(msg, type, userid){
    cutils.createModalComponent(ConfirmationModalComponent, 'castle-confirmation-modal', {
      msg: msg,
      onConfirm: function(cmp){
        utils.loading.show();
        cmp.setState({
          disabled: true
        });
        $.ajax({
          url: window.location.href,
          method: 'POST',
          data: {
            _authenticator: utils.getAuthenticator(),
            'form.button.Modify': 'true',
            'form.submitted': 'true',
            action: type,
            userid: userid
          }
        }).done(function(data){
          rebind(data);
          cmp.finishWithSuccess();
        }).always(function(){
          utils.loading.hide();
        });
      }
    });
  };

  var ResetPasswordModalComponent = cutils.Class([Modal], { // jshint ignore:line
    getInitialState: function(){
      return {
        password1: '',
        password2: ''
      };
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'preview-content-modal',
        title: 'Change user password',
        userid: '',
        login: ''
      });
    },

    handle: function(){
      utils.loading.show();
      var that = this;
      $.ajax({
        url: window.location.href,
        method: 'POST',
        data: {
          _authenticator: utils.getAuthenticator(),
          'form.button.Modify': 'true',
          'form.submitted': 'true',
          action: 'setpassword',
          userid: that.props.userid,
          password: that.state.password1
        }
      }).done(function(data){
        rebind(data);
        that.hide();
        cutils.createModalComponent(ConfirmationModalComponent, 'castle-confirmation-modal', {
          successMsg: 'Password successfully changed.'
        }).finishWithSuccess();
      }).fail(function(){
        cutils.createModalComponent(ConfirmationModalComponent, 'castle-confirmation-modal', {
          successMsg: 'Error changing password.'
        }).finishWithSuccess();
      }).always(function(){
        utils.loading.hide();
      });
    },

    sendPasswordResetEmail: function(){
      utils.loading.show();
      var that = this;
      $.ajax({
        url: window.location.href,
        method: 'POST',
        data: {
          _authenticator: utils.getAuthenticator(),
          'form.button.Modify': 'true',
          'form.submitted': 'true',
          action: 'sendpwreset',
          userid: that.props.userid
        }
      }).done(function(data){
        rebind(data);
        that.hide();
        cutils.createModalComponent(ConfirmationModalComponent, 'castle-confirmation-modal', {
          successMsg: 'Password reset email sent.'
        }).finishWithSuccess();
      }).fail(function(){
        alert('error sending password reset');
      }).always(function(){
        utils.loading.hide();
      });
    },

    valueChanged: function(name, e){
      this.state[name] = e.target.value;
      this.forceUpdate();
    },

    renderContent: function(){
      var error = '';
      if(this.state.password1 !== this.state.password2){
        error = D.div({className: "portalMessage warning"}, [
          D.strong({}, 'Warning'),
          'Passwords do not match']);
      }else if(this.state.password1.length < 5){
        error = D.div({className: "portalMessage warning"}, [
          D.strong({}, 'Warning'),
          'Must enter password']);
      }
      return D.div({ className: 'castle-reset-password'}, [
        D.p({}, 'Changing password for: ' + this.props.login),
        error,
        D.div({ className: 'form-group'}, [
          D.label({}, 'Password'),
          D.input({ value: this.state.password1, onChange: this.valueChanged.bind(this, 'password1'), type: 'password',
                    className: 'form-control'})
        ]),
        D.div({ className: 'form-group'}, [
          D.label({}, 'Repeat password'),
          D.input({ value: this.state.password2, onChange: this.valueChanged.bind(this, 'password2'), type: 'password',
                    className: 'form-control'})
        ]),
        D.div({className: "portalMessage info"}, [
          D.strong({}, 'Info'),
          'User will be required to enter new password after login'])
      ]);
    },
    renderFooter: function(){
      var that = this;
      var buttons = [];
      var disabled = false;
      if(this.state.password1 !== this.state.password2 || this.state.password1.length < 5){
        disabled = true;
      }
      buttons.push(D.button({ className: 'plone-btn plone-btn-warning',
                              onClick: that.sendPasswordResetEmail }, 'Send password reset email'));
      buttons.push(D.button({ className: 'plone-btn plone-btn-default',
                              onClick: this.hide }, 'Cancel'));
      buttons.push(D.button({ className: 'plone-btn plone-btn-danger',
                              onClick: that.handle, disabled: disabled }, 'Change password'));
      return D.div({}, buttons);
    }
  });

  var bind = function(){
    var userModal = new PloneModal($('#add-user'), { // jshint ignore:line
      actionOptions: {
        displayInModal: false,
        reloadWindowOnClose: false,
        onSuccess: function(){
          utils.loading.show();
          $.ajax({
            url: window.location.href
          }).done(function(data){
            rebind(data);
          }).fail(function(){
            window.location.reload();
          }).always(function(){
            utils.loading.hide();
          });
        }
      }
    });

    $('.castle-btn-disable-user').off('click').on('click', function(){
      executeAction(
        'Are you certain you want to disable this user? Users that are disabled are deleted from the system at another date.', 'disable', $(this).attr('data-userid'));
    });
    $('.castle-btn-resetattempts').off('click').on('click', function(){
      executeAction(
        'Are you certain you want to reset login attempt counts for this user?', 'resetattempts', $(this).attr('data-userid'));
    });
    $('.castle-btn-togglewhitelist').off('click').on('click', function(){
      executeAction(
        'Are you certain you want to '+this.value+' the Password Expiration whitelist?', 'togglewhitelist', $(this).attr('data-userid'));
    });
    $('.castle-btn-enable-user').off('click').on('click', function(){
      executeAction('Are you certain you want to enable this user?', 'enable', $(this).attr('data-userid'));
    });
    $('.castle-btn-delete-user').off('click').on('click', function(){
      executeAction('Are you certain you want to delete this user?', 'delete', $(this).attr('data-userid'));
    });
    $('.castle-btn-reset-password').off('click').on('click', function(){
      cutils.createModalComponent(ResetPasswordModalComponent, 'castle-reset-password-modal', {
        userid: $(this).attr('data-userid'),
        login: $(this).attr('data-login')
      });
    });
  };
  $(document).ready(function(){
    bind();
  });
});
