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
      this.props.failedValidation = false
      if(this.state.password1 !== this.state.password2){
        this.props.failedValidation = true
        error = D.div({className: "portalMessage warning"}, [
          D.strong({}, 'Warning'),
          'Passwords do not match']);
      }
      if(this.props.nistEnabled){
        var password = this.state.password1
        var nistLength = this.props.nistLength
        var nistUpper = this.props.nistUpper
        var nistLower = this.props.nistLower
        var nistSpecial = this.props.nistSpecial
        // Length
        if(password.length < nistLength){
          this.props.failedValidation = true
          error = D.div({className: "portalMessage warning"}, [
            D.strong({}, 'Warning'),
            `Password must be longer than ${nistLength} characters`]);
        }
        // Uppercase
        else if(password.replace(/[^A-Z]/g, "").length < nistUpper){
          this.props.failedValidation = true
          error = D.div({className: "portalMessage warning"}, [
            D.strong({}, 'Warning'),
            `Password must contain at least ${nistUpper} uppercase character(s)`]);
        }
        // Lowercase
        else if(password.replace(/[^a-z]/g, "").length < nistLower){
          this.props.failedValidation = true
          error = D.div({className: "portalMessage warning"}, [
            D.strong({}, 'Warning'),
            `Password must contain at least ${nistLower} lowercase character(s)`]);
        }
        // Special characters
        else{
          var re = new RegExp(/[@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/g, "g");
          var special = password.match(re);
          var specialLength = special ? special.length : 0
          if(specialLength < nistSpecial){
            this.props.failedValidation = true
            error = D.div({className: "portalMessage warning"}, [
              D.strong({}, 'Warning'),
              `Password must contain at least ${nistSpecial} special character(s)`]);
          }
        }
      }else{
        if(password.length < 5){
          this.props.failedValidation = true
          error = D.div({className: "portalMessage warning"}, [
            D.strong({}, 'Warning'),
            'Password must be longer than 5 characters in length.']);
        }
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
      if(this.props.failedValidation){
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
        login: $(this).attr('data-login'),
        nistEnabled: $(this).attr('data-nist-enabled'),
        nistLength: $(this).attr('data-nist-length'),
        nistUpper: $(this).attr('data-nist-upper'),
        nistLower: $(this).attr('data-nist-lower'),
        nistSpecial: $(this).attr('data-nist-special'),
      });
    });
  };
  $(document).ready(function(){
    bind();
  });
});
