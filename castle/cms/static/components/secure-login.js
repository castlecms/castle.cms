require([
  'jquery',
  'castle-url/libs/react/react',
  'mockup-utils'
], function($, R, utils){
  'use strict';

  var D = R.DOM;

  var C = function(name){
    // generate namespaced classes
    return 'castle-secure-login-' + name;
  };

  var STATES = {
    NO_WHERE: 'request-auth-code',
    CODE_SENT: 'auth-code-sent',
    CODE_AUTHORIZED: 'code-authorized',
    CHANGE_PASSWORD: 'change-password',
    COUNTRY_BLOCKED: 'country-blocked',
    COUNTRY_BLOCK_REQUESTED: 'country-block-requested',
    RESET_PASSWORD: 'reset-password',
  };

  var SecureLoginComponent = R.createClass({
    getInitialState: function(){
      return {
        username: '',
        code: '',
        password: '',
        new_password1: '',
        new_password2: '',
        authType: 'email',
        state: this.props.twoFactorEnabled && STATES.NO_WHERE || STATES.CODE_AUTHORIZED,
        message: null,
        messageType: 'info',
        authenticator: '',
        counter: 0
      };
    },

    getDefaultProps: function(){
      return {
        supportedAuthSchemes: [{
          id: 'email',
          label: 'Email'
        }],
        twoFactorEnabled: false
      };
    },

    api: function(data, success){
      var that = this;
      data.username = that.state.username;

      utils.loading.show();
      $.ajax({
        url: that.props.apiEndpoint,
        method: 'POST',
        data: data
      }).done(function(data){
        var messageType = 'info';
        if(data.success){
          if(success){
            success(data);
          }
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
          message: 'An unknown error occurred attempting to login',
          messageType: 'danger'
        });
      });
    },

    getAuthScheme: function(id){
      for(var i=0; i<this.props.supportedAuthSchemes.length; i++){
        if(this.props.supportedAuthSchemes[i].id === id){
          return this.props.supportedAuthSchemes[i];
        }
      }
    },

    valueChanged: function(attr, e){
      var state = {};
      state[attr] = e.target.value;
      this.setState(state);
    },

    authTypeSelected: function(type){
      this.setState({
        authType: type.id
      });
    },

    sendAuthCode: function(e){
      var that = this;
      e.preventDefault();
      that.api({
        authType: that.state.authType,
        apiMethod: 'send_authorization'
      }, function(){
        that.setState({
          state: STATES.CODE_SENT
        });
      });
    },

    authorizeCode: function(e){
      var that = this;
      e.preventDefault();
      that.api({
        code: that.state.code,
        apiMethod: 'authorize_code'
      }, function(){
        that.setState({
          state: STATES.CODE_AUTHORIZED
        });
      });
    },

    login: function(e){
      var that = this;
      e.preventDefault();
      that.api({
        password: that.state.password,
        code: that.state.code,
        apiMethod: 'login'
      }, function(data){
        if(data.countryBlocked){
          that.setState({
            state: STATES.COUNTRY_BLOCKED
          });
        } else if(data.resetpassword){
          // need to show reset password form now
          that.setState({
              state: STATES.CHANGE_PASSWORD,
              message: 'Login successful.',
              messageType: 'info',
              authenticator: data.authenticator
            }
          );
        } else {
          // continue to site
          that.setState({
            state: STATES.CODE_AUTHORIZED,
            message: 'Login successful.',
            messageType: 'info'
          }, function(){
            window.location = that.props.successUrl;
          });
        }
      });
    },

    set_password: function(e){
      var that = this;
      e.preventDefault();
      that.api({
        username: that.state.username,
        existing_password: that.state.existing_password,
        new_password: that.state.new_password1,
        _authenticator: that.state.authenticator,
        apiMethod: 'set_password'
      }, function(){
        // continue to site
        that.setState({
          message: 'Password changed.',
          messageType: 'info'
        }, function(){
          window.location = that.props.successUrl;
        });
      });
    },

    request_country_exception: function(e){
      var that = this;
      e.preventDefault();
      that.api({
        password: that.state.password,
        code: that.state.code,
        _authenticator: that.state.authenticator,
        apiMethod: 'request_country_exception'
      }, function(data){
        if(data.success){
          that.setState({
            state: STATES.COUNTRY_BLOCK_REQUESTED
          });
        }
      });
    },

    checkEnterHit: function(submissionFunction, e){
      if (e.which == 13 || e.keyCode == 13) {
        submissionFunction.apply(this, [e]);
      }
    },

    renderAuthSelector: function(){
      var that = this;
      if(that.props.supportedAuthSchemes.length <= 1){
        return '';
      }
      return D.div({ className: 'form-group'}, [
        D.label({ htmlFor: 'authType' }, 'Authorize with:'),
        that.props.supportedAuthSchemes.map(function(scheme){
          return D.div({ className: 'radio'}, D.label({}, D.input({
            type: 'radio', name: 'authType',
            checked: that.state.authType === scheme.id,
            onClick: that.authTypeSelected.bind(that, scheme)
          }, scheme.label)));
        })
      ]);
    },

    renderUsername: function(submissionFunction){
      var that = this;

      // for calculating ids
      that.state.counter += 1;

      var disabled = that.props.twoFactorEnabled && that.state.state !== STATES.NO_WHERE;
      if(that.state.state === STATES.RESET_PASSWORD){
        disabled = true;
      }
      return D.div({ className: 'form-group'}, [
        D.label({ htmlFor: 'username' + that.state.counter }, 'Username'),
        D.input({type: 'text', value: that.state.username,
                 className: 'form-control username',
                 id: 'username' + that.state.counter,
                 placeholder:'Enter username', disabled: disabled,
                 onKeyUp: that.checkEnterHit.bind(that, submissionFunction),
                 onChange: that.valueChanged.bind(that, 'username')})
      ]);
    },

    renderInitialView: function(message){
      var that = this;
      var authType = that.getAuthScheme(that.state.authType);
      return D.div({className: C('form-' + STATES.NO_WHERE)}, [
        D.h2({ className: 'auth-title' }, 'Login with Two-Factor Authorization'),
        D.p({ className: 'auth-description' },
              'Before you can login with your password, we need you to verify ' +
              'who you are by sending you an authorization code.'),
        that.renderUsername(that.sendAuthCode),
        that.renderAuthSelector(),
        D.div({ className: C('buttons')}, [
          D.button({ className: C('send-auth-button') + ' btn btn-default',
                     disabled: that.state.username.length === 0,
                     onClick: that.sendAuthCode }, 'Send authorization code via ' + authType.label.toLowerCase()),
        ]),
        message
      ]);
    },

    renderCodeAuthView: function(message){
      var that = this;
      return D.div({className: C('form-' + STATES.CODE_SENT)}, [
        D.h2({ className: 'auth-title' }, 'Login with Two-Factor Authorization'),
        D.p({ className: 'auth-description' },
              'Now please verify the authorization code we sent you.'),
        that.renderUsername(that.authorizeCode),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'code' }, 'Authorization code'),
          D.input({type: 'text', value: that.state.code,
                   className: 'form-control', id: 'code', placeholder:'Enter code',
                   onChange: that.valueChanged.bind(that, 'code'),
                   onKeyUp: that.checkEnterHit.bind(that, that.authorizeCode)})
        ]),
        D.div({ className: C('buttons')}, [
          D.button({ className: C('resend-button') + ' btn btn-default',
                     onClick: function(e){
                       e.preventDefault();
                       that.setState({
                         state: STATES.NO_WHERE,
                         code: '',
                         password: ''
                       });
                     } }, 'Re-send code'),
          D.button({ className: C('send-auth-button') + ' btn btn-primary',
                     onClick: that.authorizeCode }, 'Authorize code'),
        ]),
        message
      ]);
    },

    renderPasswordForm: function(message){
      var that = this;
      that.state.counter += 1;
      var disabled = false;
      if(!that.state.username || !that.state.password){
        disabled = true;
      }

      var help = 'Now please login with your username and password.';
      if(!that.props.twoFactorEnabled){
        help = 'Login with username and password';
      }
      return D.div({className: C('form-' + STATES.CODE_AUTHORIZED)}, [
        D.h2({ className: 'auth-title' }, 'Login'),
        D.p({ className: 'auth-description' }, help),
        that.renderUsername(that.login),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password' + that.state.counter}, 'Password'),
          D.input({type: 'password', value: that.state.password,
                   className: 'form-control password', id: 'password' + that.state.counter,
                   placeholder:'Enter password',
                   onKeyUp: that.checkEnterHit.bind(that, that.login),
                   onChange: that.valueChanged.bind(that, 'password')})
        ]),
        D.div({ className: C('buttons')}, [
          D.button({ className: C('login-button') + ' btn btn-primary',
                     onClick: that.login, disabled: disabled }, 'Login'),
        ]),
        message
      ]);
    },

    pwChangeValueChanged: function(name, e){
      var that = this;
      that.state[name] = e.target.value;
      if(that.state.new_password1 !== that.state.new_password2){
        that.state.messageType = 'warning';
        that.state.message = 'Passwords do not match.';
      } else if(that.state.new_password1.length < 7){
        that.state.messageType = 'warning';
        that.state.message = 'Password needs to be at least 8 characters.';
      } else {
        that.state.messageType = 'info';
        that.state.message = 'Valid password.';
      }
      that.forceUpdate();
    },

    renderChangeForm: function(message){
      var that = this;
      that.state.counter += 1;
      var help = 'Your password needs to be changed. ' +
                 'Passwords must match and be at least 8 characters long.';
      var disabled = false;
      if(that.state.new_password1 !== that.state.new_password2){
        disabled = true;
      } else if(that.state.new_password1.length < 7){
        disabled = true;
      }
      var onKeyUp = that.checkEnterHit.bind(that, that.set_password);
      if(disabled){
        onKeyUp = function(){};
      }
      return D.div({className: C('form-' + STATES.RESET_PASSWORD) + ' ' + C('form-' + STATES.CHANGE_PASSWORD)}, [
        D.h2({ className: 'auth-title' }, 'Change password'),
        D.p({ className: 'auth-description' }, help),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'username1' + that.state.counter}, 'Username'),
          D.input({type: 'text', value: that.state.username, disabled: true,
                   className: 'form-control', id: 'username1' + that.state.counter})
        ]),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password1' + that.state.counter}, 'Existing password'),
          D.input({type: 'password', value: that.state.password1,
                   disabled: that.state.state !== STATES.CHANGE_PASSWORD,
                   onChange: that.pwChangeValueChanged.bind(that, 'existing_password'),
                   className: 'form-control', id: 'password1' + that.state.counter})
        ]),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password2' + that.state.counter }, 'New password'),
          D.input({type: 'password', value: that.state.new_password1,
                   className: 'form-control password2', id: 'password2' + that.state.counter,
                   placeholder:'Enter new password', onKeyUp: onKeyUp,
                   onChange: that.pwChangeValueChanged.bind(that, 'new_password1'),
                   disabled: that.state.state !== STATES.CHANGE_PASSWORD})
        ]),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password3' + that.state.counter }, 'Confirm new password'),
          D.input({type: 'password', value: that.state.new_password2,
                   className: 'form-control password3', id: 'password3' + that.state.counter,
                   placeholder:'Confirm new password', onKeyUp: onKeyUp,
                   onChange: that.pwChangeValueChanged.bind(that, 'new_password2'),
                   disabled: that.state.state !== STATES.CHANGE_PASSWORD})
        ]),
        D.div({ className: C('buttons')}, [
          D.button({ className: C('login-button') + ' btn btn-primary',
                     disabled: disabled,
                     onClick: that.set_password }, 'Change password'),
        ]),
        message
      ]);
    },

    renderCountryBlockedForm: function(message){
      var that = this;
      var help = 'You are logging in from a country that is blocked. ' +
                 'You can request to be temporarily allowed to access from ' +
                 'your current location. Once your request is approved, ' +
                 'you will be sent an email letting you know that you are ' +
                 'able to login again. Your temporary allowed access from ' +
                 'your current location only works for the current computer, ' +
                 'browser and location you are accessing the site from.';
      return D.div({className: C('form-' + STATES.COUNTRY_BLOCKED)}, [
        D.h2({ className: 'auth-title' }, 'Request access from blocked country'),
        D.p({ className: 'auth-description' }, help),
        D.div({ className: C('buttons')}, [
          D.button({ className: C('login-button') + ' btn btn-primary',
                     onClick: that.request_country_exception,
                     disabled: that.state.state !== STATES.COUNTRY_BLOCKED
                   }, 'Request access'),
        ]),
        message
      ]);
    },

    renderCountryBlockedRequested: function(message){
      var help = 'You have requested a block exception. Administrators will ' +
                 'review your reqeust. Once you are approved, you will receive ' +
                 'an email letting you know that you are allowed to login again.';
      return D.div({className: C('form-' + STATES.COUNTRY_BLOCK_REQUESTED)}, [
        D.h2({ className: 'auth-title' }, 'Requested access from blocked country'),
        D.p({ className: 'auth-description' }, help),
        message
      ]);
    },

    componentDidUpdate: function(){
      this.update();
    },

    componentDidMount: function(){
      this.update();
    },

    update: function(){
      var $container = $(this.refs.container.getDOMNode());
      var $selectedForm = $('.' + C('form-' + this.state.state));

      setTimeout(function(){
        $container.height($selectedForm.height() + 20);
      }, 500);

      if(this.state.state !== this.state.last_state){
        $('input:visible:first', $selectedForm).focus();
      }
      this.state.last_state = this.state.state;
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
        that.renderInitialView(message),
        that.renderCodeAuthView(message),
        that.renderPasswordForm(message),
        that.renderChangeForm(message),
        that.renderCountryBlockedForm(message),
        that.renderCountryBlockedRequested(message)
      ];

      return D.div({ className: C('container'), ref: 'container'}, [
        D.div({ className: C('forms-container') + ' ' + that.state.state,
                ref: 'formContainer'}, forms)
      ]);
    }
  });

  var PasswordResetComponent = R.createClass({
    getInitialState: function(){
      return {
        new_password1: '',
        new_password2: '',
        state: STATES.RESET_PASSWORD,
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
      } else if(that.state.new_password1.length < 7){
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
                 'request link and intend to reset your password(user id: ' +
                 that.props.username + '). Do not fill out this ' +
                 'form is that was not your intention.';
      var disabled = false;
      if(that.state.new_password1 !== that.state.new_password2){
        disabled = true;
      } else if(that.state.new_password1.length < 7){
        disabled = true;
      }
      return D.div({className: C('form-' + STATES.RESET_PASSWORD)}, [
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
        D.div({ className: C('buttons')}, [
          D.button({ className: C('login-button') + ' btn btn-primary',
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
          apiMethod: 'reset_password'
        }
      }).done(function(data){
        var messageType = 'info';
        if(data.success){
          // we're good!
          that.setState({
            message: 'Password successfully changed. You may now login',
            messageType: 'info'
          }, function(){
            setTimeout(function(){
              window.location = window.location.href.split('?')[0];
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
          message: 'An unknown error occurred attempting to login',
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

      return D.div({ className: C('container'), ref: 'container'}, [
        D.div({ className: C('forms-container') + ' ' + that.state.state,
                ref: 'formContainer'}, forms)
      ]);
    }
  });

  var el = document.getElementById('secure-login');
  var options = JSON.parse(el.getAttribute('data-options'));

  if(options.passwordReset){
    R.render(R.createElement(PasswordResetComponent, options), el);
  }else{
    R.render(R.createElement(SecureLoginComponent, options), el);
  }
});
