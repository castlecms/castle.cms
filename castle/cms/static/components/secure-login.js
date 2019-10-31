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

  var STATES = {
    REQUEST_AUTH_CODE: 'request-auth-code',
    CHECK_CREDENTIALS: 'check-credentials',
    COUNTRY_BLOCKED: 'country-blocked',
    COUNTRY_BLOCK_REQUESTED: 'country-block-requested',
    RESET_PASSWORD: 'reset-password',
  };

  var SecureLoginComponent = R.createClass({
    getInitialState: function(){
      if (this.props.twoFactorEnabled){
        var initialState = STATES.REQUEST_AUTH_CODE;
      } else {
        var initialState = STATES.CHECK_CREDENTIALS;
      }
      return {
        username: '',
        code: '',
        password: '',
        new_password1: '',
        new_password2: '',
        authType: 'email',
        state: initialState,
        message: null,
        messageType: 'info',
        authenticator: '',
        counter: 0,
      };
    },

    getDefaultProps: function(){
      return {
        supportedAuthSchemes: [{
          id: 'email',
          label: 'Email'
        }],
        twoFactorEnabled: false,
        additionalProviders: [],
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

    // sendAuthCode: function(e){
    //   var that = this;
    //   e.preventDefault();
    //   that.api({
    //     authType: that.state.authType,
    //     apiMethod: 'send_authorization'
    //   }, function(){
    //     that.setState({
    //       state: STATES.CODE_SENT
    //     });
    //   });
    // },
    //
    // authorizeCode: function(e){
    //   var that = this;
    //   e.preventDefault();
    //   that.api({
    //     code: that.state.code,
    //     apiMethod: 'authorize_code'
    //   }, function(){
    //     that.setState({
    //       state: STATES.CODE_AUTHORIZED
    //     });
    //   });
    // },

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

    renderAdditionalLoginProviders: function(){
      var that = this;
      var additional = [];
      if (that.props.additionalProviders.length > 0) {
        additional.push(D.hr());
        var providers = [];
        that.props.additionalProviders.forEach(function(provider) {
          providers.push(D.li({}, D.a({ href: provider.url }, [
            D.img({ src: provider.logo }),
            provider.label,
          ])));
        });
        additional.push(D.ul(
          { className: getClass('login-provider') }, providers))
      }
      return additional;
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
      ].concat(that.renderAdditionalLoginProviders()));
    },

    renderUsername: function(submissionFunction){
      var that = this;

      // for calculating ids
      that.state.counter += 1;

      var disabled = that.props.twoFactorEnabled && that.state.state !== STATES.REQUEST_AUTH_CODE;
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

    renderCodeAuthField: function(){
      var resend_auth = function(event) {
        e.preventDefault();
        that.setState({
          state: STATES.REQUEST_AUTH_CODE,
          code: '',
          password: ''
        });
      }
      return D.div({ className: 'form-group'}, [
        D.label({ htmlFor: 'code' },'Authorization code'),
        D.input({type: 'text', value: that.state.code,
                 className: 'form-control', id: 'code', placeholder:'Enter code',
                 onChange: that.valueChanged.bind(that, 'code')
               }),
        D.button({ className: getClass('resend-button') + ' btn btn-default',
                   onClick: resend_auth }, 'Resend Code')
                 ])
    },

    renderTwoFactorView: function(message){
      var that = this;
      var authType = that.getAuthScheme(that.state.authType);
      return D.div({className: getClass('form-' + STATES.REQUEST_AUTH_CODE)}, [
                      D.h2({ className: 'auth-title' }, 'Login with Two-Factor Authorization'),
                      D.p({ className: 'auth-description' },
                            'Before you can login with your password, we need you to verify ' +
                            'who you are by sending you an authorization code.'),
                      that.renderUsername(that.sendAuthCode),
                      that.renderAuthSelector(),
                      D.div({ className: getClass('buttons')},
                        D.button({ className: getClass('send-auth-button') + ' btn btn-default',
                                   disabled: that.state.username.length === 0,
                                   onClick: that.sendAuthCode }, 'Send authorization code via ' + authType.label.toLowerCase()),
                      ),
                      message,
                      that.renderAdditionalLoginProviders()
      ]);
    },

    renderCheckCredentials: function(message){
      var that = this;
      that.state.counter += 1;
      var disabled = false;
      if(!that.state.username || !that.state.password){
        disabled = true;
      }

      var help = 'Login with your username, password, and Two-Factor Code.';
      if(!that.props.twoFactorEnabled){
        help = 'Login with username and password';
      }

      var buttonDiv = D.div({ className: getClass('buttons')}, [
                        D.button({ className: getClass('login-button') + ' btn btn-primary',
                                    onClick: that.login, disabled: disabled }, 'Login'),]);

      var credentialFields = [
        that.renderUsername(that.login),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password' + that.state.counter}, 'Password'),
          D.input({type: 'password', value: that.state.password,
                   className: 'form-control password', id: 'password' + that.state.counter,
                   placeholder:'Enter password',
                   onKeyUp: that.checkEnterHit.bind(that, that.login),
                   onChange: that.valueChanged.bind(that, 'password')})
        ]),
      ]
      if (that.props.twoFactorEnabled){
        credentialFields.push(that.renderCodeAuthField());
      }
      credentialFields.push(buttonDiv);
      credentialFields.push(message);
      credentialFields.push(that.renderAdditionalLoginProviders())

      var credentialForm = D.div({className: getClass('form-' + STATES.CHECK_CREDENTIALS)}, [
        D.h2({ className: 'auth-title' }, 'Login'),
        D.p({ className: 'auth-description' }, help)].concat(credentialFields));
      return credentialForm;
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
      return D.div({className: getClass('form-' + STATES.COUNTRY_BLOCKED)}, [
        D.h2({ className: 'auth-title' }, 'Request access from blocked country'),
        D.p({ className: 'auth-description' }, help),
        D.div({ className: getClass('buttons')}, [
          D.button({ className: getClass('login-button') + ' btn btn-primary',
                     onClick: that.request_country_exception,
                     disabled: that.state.state !== STATES.COUNTRY_BLOCKED
                   }, 'Request access'),
        ]),
        message
      ]);
    },

    renderCountryExceptionRequested: function(message){
      var help = 'You have requested a block exception. Administrators will ' +
                 'review your reqeust. Once you are approved, you will receive ' +
                 'an email letting you know that you are allowed to login again.';
      return D.div({className: getClass('form-' + STATES.COUNTRY_BLOCK_REQUESTED)}, [
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
      var $selectedForm = $('.' + getClass('form-' + this.state.state));

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
        that.renderTwoFactorView(message),
        that.renderCheckCredentials(message),
        that.renderCountryBlockedForm(message),
        that.renderCountryExceptionRequested(message)
      ];

      return D.div({ className: getClass('container'), ref: 'container'}, [
        D.div({ className: getClass('forms-container') + ' ' + that.state.state,
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
      return D.div({className: getClass('form-' + STATES.RESET_PASSWORD)}, [
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
          apiMethod: 'reset_password'
        }
      }).done(function(data){
        var messageType = 'info';
        if(data.success){
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

      return D.div({ className: getClass('container'), ref: 'container'}, [
        D.div({ className: getClass('forms-container') + ' ' + that.state.state,
                ref: 'formContainer'}, forms)
      ]);
    }
  });

  var el = document.getElementById('secure-login');
  var options = JSON.parse(el.getAttribute('data-options'));
  //if(options.passwordReset){
  //  R.render(R.createElement(PasswordResetComponent, options), el);
  //}else{
  // ^ this will either be one of the existing component forms, or a different file entirely
  R.render(R.createElement(SecureLoginComponent, options), el);
  //}
});
