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
    REQUEST_AUTH_CODE: 'requesting-auth-code',
    CHECK_CREDENTIALS: 'check-credentials',
    COUNTRY_BLOCKED: 'country-blocked',
    COUNTRY_BLOCK_REQUESTED: 'country-block-requested',
    CHANGE_PASSWORD: 'change-password',
  };

  var SecureLoginComponent = R.createClass({

    getInitialState: function(){
      return {
        username: '',
        code: '',
        password: '',
        authType: 'email',
        state: this.props.state,
        message: null,
        messageType: 'info',
        authenticator: '',
        last_state: STATES.REQUEST_AUTH_CODE,
      };
    },

    getDefaultProps: function(){
      return {
        supportedAuthSchemes: [{
          id: 'email',
          label: 'Email'
        }],
        twoFactorEnabled: false,
        state: STATES.CHECK_CREDENTIALS,
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
          if (data.passwordExpired) {
            setTimeout(function(){
                window.location = data.changePasswordUrl;
              }, 1500);
          }
          var newState = that.state.state;
          if(data.state){
            newState = data.state;
          }
          that.setState({
            state: newState,
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

    sendAuthCode: function(){
        var that = this;
        var authSent = function(data){
          that.setState({
            state: STATES.CHECK_CREDENTIALS,
            message: data.message,
            messageType: 'info'
          })
        }
        that.api({
          authType: that.state.authType
        }, authSent);
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

    login: function(e){
      var that = this;
      e.preventDefault();
      that.api({
        password: that.state.password,
        code: that.state.code,
      }, function(data){
        if(data.countryBlocked){
          that.setState({
            state: STATES.COUNTRY_BLOCKED
          });
        } else {
          if(data.success){
            that.setState({
              message: 'Login successful.',
              messageType: 'info'
            });
            window.location = that.props.successUrl;
          } else {
            that.setState({
              message: data.message,
              messageType: 'danger'
            })
          }
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
            state: STATES.COUNTRY_BLOCK_REQUESTED,
            message: data.message
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

      var disabled = that.props.twoFactorEnabled && that.state.state !== STATES.REQUEST_AUTH_CODE;
      var nameField = D.input({
        type: 'text',
        value: that.state.username,
        className: 'form-control username',
        id: 'username',
        placeholder:'Enter username',
        disabled: disabled,
        onKeyUp: that.checkEnterHit.bind(that, submissionFunction),
        onChange: that.valueChanged.bind(that, 'username'),
        autoCorrect: 'off',
        autoCapitalize: 'none',
      })
      return D.div({ className: 'form-group'}, [
        D.label({ htmlFor: 'username' }, 'Username'),
        nameField
      ]);
    },

    renderCodeAuthField: function(){
      var that = this;
      return D.div({ className: 'form-group'}, [
        D.label({ htmlFor: 'code' },'Authorization code'),
        D.input({type: 'text', value: that.state.code,
                 className: 'form-control', id: 'code', placeholder:'Enter code',
                 onKeyUp: that.checkEnterHit.bind(that, that.login),
                 onChange: that.valueChanged.bind(that, 'code')
               })
        ])
    },

    renderResendButton: function(){
      var that = this;
      var resend_auth = function(event) {
        event.preventDefault();
        that.api({'apiMethod':'resendAuth'},
          function(data){
            if(data.success){
              that.setState({
                state: STATES.REQUEST_AUTH_CODE,
                message: data.message,
                messageType: 'info',
                code: '',
                password: ''
              });
            }
          });
      }
      return D.button({ className: getClass('resend-button') + ' btn btn-default',
                                onClick: resend_auth }, 'Resend Code');
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
      var disabled = false;
      if(!that.state.username || !that.state.password){
        disabled = true;
      }

      var help = 'Login with your username, password, and Two-Factor Code.';
      if(!that.props.twoFactorEnabled){
        help = 'Login with username and password';
      }

      var buttons = [D.button({ className: getClass('login-button') + ' btn btn-primary',
                                onClick: that.login, disabled: disabled }, 'Login')]

      var credentialFields = [
        that.renderUsername(that.login),
        D.div({ className: 'form-group'}, [
          D.label({ htmlFor: 'password'}, 'Password'),
          D.input({type: 'password', value: that.state.password,
                   className: 'form-control password', id: 'password',
                   placeholder:'Enter password',
                   onKeyUp: that.checkEnterHit.bind(that, that.login),
                   onChange: that.valueChanged.bind(that, 'password')})
        ]),
      ]
      var resendButton = '';
      if (that.props.twoFactorEnabled){
        resendButton = that.renderResendButton();
        credentialFields.push(that.renderCodeAuthField());
      }
      buttons.push(resendButton);

      var buttonDiv = D.div({ className: getClass('buttons')}, buttons);
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
        var $oldForm = $('.' + getClass('form-' + this.state.last_state));
        $oldForm.hide();
        $selectedForm.show();
        $selectedForm.focus();
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
      var forms = [];
      if (that.props.twoFactorEnabled){
        forms.push(that.renderTwoFactorView(message));
      }
      forms.push(that.renderCheckCredentials(message));
      forms.push(that.renderCountryBlockedForm(message));
      forms.push(that.renderCountryExceptionRequested(message));

      return D.div({ className: getClass('container'), ref: 'container'}, [
        D.div({ className: getClass('forms-container') + ' ' + that.state.state,
                ref: 'formContainer'}, forms)
      ]);
    }
  });

  var el = document.getElementById('secure-login');
  var options = JSON.parse(el.getAttribute('data-options'));

  R.render(R.createElement(SecureLoginComponent, options), el);

});
