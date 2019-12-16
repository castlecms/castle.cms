require([
  'jquery',
  'castle-url/libs/react/react',
  'mockup-utils'
], function($, R, utils){
  'use strict';

  var D = R.DOM;

  var getClass = function(name){
    // generate namespaced classes
    return 'castle-secure-login-' + name;
  };

  var PasswordResetComponent = R.createClass({
    getInitialState: function(){
      return {
        new_password1: '',
        new_password2: '',
        message: null,
        messageType: 'info'
      };
    },

    pwResetValueChanged: function(name, e){
      var that = this;
      that.state[name] = e.target.value;
      if(that.state.new_password1 !== that.state.new_password2){
        that.state.messageType = 'warning';
        that.state.message = 'Passwords do not match.';
      } else if(that.state.new_password1.length < 8){
        that.state.messageType = 'warning';
        that.state.message = 'Password needs to be at least 8 characters.';
      } else {
        that.state.messageType = 'info';
        that.state.message = 'Valid password.';
      }
      that.forceUpdate();
    },

    renderView: function(message){
      var that = this;
      that.state.counter += 1;
      var help = 'You should only be here if you have clicked on a password reset ' +
                 'request link and intend to reset your password. Do not fill out this ' +
                 'form if this was not your intention.';
      var disabled = false;
      if(that.state.new_password1 !== that.state.new_password2){
        disabled = true;
      } else if(that.state.new_password1.length < 8){
        disabled = true;
      }
      return D.div({className: getClass('form-reset-password')}, [
        D.h2({ className: 'auth-title' }, 'Change password'),
        D.p({ className: 'auth-description' }, help),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password1' }, 'New password'),
          D.input({type: 'password', value: that.state.new_password1,
                   className: 'form-control password2', id: 'password1',
                   placeholder:'Enter new password',
                   onChange: that.pwResetValueChanged.bind(that, 'new_password1')})
        ]),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password2' }, 'Confirm new password'),
          D.input({type: 'password', value: that.state.new_password2,
                   className: 'form-control password3', id: 'password2',
                   placeholder:'Confirm new password',
                   onChange: that.pwResetValueChanged.bind(that, 'new_password2')})
        ]),
        D.div({ className: getClass('buttons')}, [
          D.button({ className: getClass('login-button') + ' btn btn-primary',
                     disabled: disabled,
                     onClick: that.set_password }, 'Change password'),
        ]),
        message
      ]);
    },

    set_password: function(e){
      var that = this;
      e.preventDefault();

      utils.loading.show();
      $.ajax({
        url: that.props.apiEndpoint,
        method: 'POST',
        data: {
          password: that.state.new_password2,
          code: that.props.code,
          userid: that.props.userid,
        }
      }).done(function(data){
        var messageType = 'info';
        if(data.success){
          that.setState({
            message: 'Password successfully changed. You may now login',
            messageType: 'info'
          }, function(){
            setTimeout(function(){
              window.location = that.props.successUrl;
            }, 1500);
          });
        }else{
          messageType = 'danger';
        }
        if(data.message){
          that.setState({
            message: data.message,
            messageType: messageType
          });
        }
      }).always(function(){
        utils.loading.hide();
      }).fail(function(){
        that.setState({
          message: 'An unknown error occurred attempting to reset password.',
          messageType: 'danger'
        });
      });
    },

    render: function(){
      var that = this;

      var message = '';
      if(that.state.message){
        message = D.div({ className: "alert alert-" + that.state.messageType,
                          role: "alert", ref: 'alert' }, [
          that.state.message
        ]);
      }

      var forms = [
        that.renderView(message)
      ];

      return D.div({ className: getClass('container'), ref: 'container'}, [
        D.div({ className: getClass('forms-container') + ' ' + that.state.state,
                ref: 'formContainer'}, forms)
      ]);
    }
  });

  var el = document.getElementById('password-reset');
  var options = JSON.parse(el.getAttribute('data-options'));

  R.render(R.createElement(PasswordResetComponent, options), el);
});
