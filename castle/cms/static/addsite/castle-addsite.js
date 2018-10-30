require([
  'jquery',
  'castle-url/libs/react/react.min',
  'castle-url/addsite/inputs',
  'castle-url/addsite/dispatcher',
  'castle-url/addsite/store',
  'castle-url/libs/object-assign'
], function($, React, ReactFormInputs, Dispatcher, Store, assign){
  'use strict';

var D = React.DOM;

var phases = [
  'Setup',
  'Site Settings',
  'Social Media',
  'API Settings'
];

var appStore = assign({}, Store);

var siteSetup = React.createClass({
  parseExtensions: function() {
    var extensions = this.props.initial.extensions;
    var extension_values = {};

    for( var ex in extensions ) {
      var item = extensions[ex];
      extension_values[ex] = item.checked;
    }

    return extension_values;
  },
  exportExtensions: function() {
    var extensions = appStore.get('extension_ids');
    var included = [];

    for( var ex in extensions ) {
      var val = extensions[ex];
      if( val === true ) {
        included.push(ex);
      }
    }

    return included;

  },
  componentDidUpdate: function(prevProps, prevState) {

    if( this.state.previous_phase !== prevState.phase ) {
      this.setState({
        previous_phase: prevState.phase
      });
    }
  },
  componentWillMount: function() {
    appStore.initialize(this.state.data);
  },
  getInitialState: function() {
    return {
      "data": {
        'site_id': 'Castle',
        'title': 'site',
        'default_language': 'en-us',
        'portal_timezone': jstz.determine().name(),
        'extension_ids': this.parseExtensions()
      },
      "timer": [0],
      "phase": 1,
      "previous_phase": 1,
      "valid": true,
      "advanced": this.props.initial.advanced,
      "url": null
    };
  },
  validate: function(state) {
    this.setState({
      valid: state
    });
  },
  goBack: function(e) {
    e.preventDefault();

    if( !this.checkFields() ) {
      return;
    }

    var phase = this.state.phase - 1;

    this.setState({
      phase: phase
    });
  },
  goForward: function(e) {
    e.preventDefault();

    if( !this.checkFields() ) {
      return;
    }

    var phase = this.state.phase+1;

    this.setState({
      phase: phase,
      errors: null
    });
  },
  skipConfig: function(e) {
    e.preventDefault();
    if( this.state.complete ) {
      window.location = this.state.url;
    }
  },
  createButtons: function() {
    var buttons = [];
    var disabled = '';
    var btnClass = "btn btn-primary";
    if( this.state.valid === false ) {
      disabled = 'disabled';
      btnClass += " disabled";
    }

    if( this.state.phase > 2 ) {
      buttons.push(
        D.button({
          className: btnClass,
          disabled: disabled,
          onClick: this.goBack
        }, [
          D.span({
            className: "glyphicon glyphicon-chevron-left glyph-left"
          }),
          "Back"
        ])
      );
    }

    if( this.state.phase === 1 ) {
      buttons.push(
        D.button({
          className: btnClass,
          disabled: disabled,
          onClick: this.submitInitialForm,
        }, [
            "Build Site",
            D.span({
              className: "glyphicon glyphicon-wrench glyph-right"
            })
          ]
        )
      );

      var modeText = 'Advanced settings';
      if( this.state.advanced ) {
        modeText = 'Simple mode';
      }
      buttons.push(
        D.a({
          className: "sit-right",
          onClick: this.toggleAdvanced
        }, modeText)
      );
    }

    if( this.state.phase < phases.length && this.state.phase > 1 ) {
      buttons.push(
        D.button({
          className: btnClass + " sit-right",
          disabled: disabled,
          onClick: this.goForward
        }, [
            "Next",
            D.span({
              className: "glyphicon glyphicon-chevron-right glyph-right"
            })
        ])
      );
    }

    if( this.state.phase === phases.length ) {

      var buttonContents = [
        "Save & Continue",
        D.span({
          className: "glyphicon glyphicon-ok glyph-right"
        })
      ];

      if( !this.state.complete ) {
        disabled = "disabled";
        buttonContents = "Building site...";
      }

      buttons.push(
        D.button({
          className: btnClass + " btn-success sit-right",
          disabled: disabled,
          onClick: this.submitConfigurations
        }, buttonContents)
      );
    }else if( this.state.complete ) {
      buttons.push(
        D.button({
          className: btnClass + " btn-success sit-right",
          disabled: disabled,
          onClick: this.skipConfig
        }, "Skip configuration")
      );
    }
    return D.div({
      className: 'buttonBox'
    }, buttons);
  },
  createTabs: function() {
    var tabs = [];
    if( this.state.phase === 1 ) {
      return '';
    }

    for( var index in phases ) {
      var className = "";
      var disabled = "";

      var phase = parseInt(index) + 1;

      if( phase === 1 ) {
        //Don't want to include the setup page
        continue;
      }

      if( this.state.phase == phase ) {
        className = "active";
      }

      //Something is invalid
      var invalid = (this.state.valid === false);


      if( invalid ) {
        className += " disabled";
        disabled = "disabled";
      }

      tabs.push(
        D.li({
          className: className,
          role: "presentation"
        }, D.a({
          href: "#",
          'data-phase': phase,
          disabled: disabled,
          onClick: this.tabChange
        }, phases[index]))
      );
    }

    return D.ul({
      className: "nav nav-tabs"
    }, tabs);
  },
  createInput: function(props) {
    var type = null;
    if( props.type == "select") {
      type = ReactFormInputs.select;
    }
    else if( props.type == "fieldset" ) {
      type = ReactFormInputs.fieldset;
    }
    else if( props.type == "file" ) {

      if( props.isImage ) {

        var data = appStore.get(props.name);
        if( data ) {
          props.title = data.filename;
          props.image = data.filedata;
        }
      }
      type = ReactFormInputs.file;
    }
    else if( props.type == "checkbox" ) {
      type = ReactFormInputs.checkbox;
      var checked = appStore.get(props.name);

      //If it isn't set in the appStore, don't touch it
      if( checked === true ) {
        props.checked = true;
      }else if( checked === false ){
        props.checked = false;
      }
    }
    else {
      type = ReactFormInputs.input;
    }
    props.initialize = appStore.add;
    props.validate = this.validate;

    props.timer = this.state.timer;
    props.ref = props.name;

    props.key = props.key || props.name;
    props.defaultValue = props.defaultValue || appStore.get(props.name);

    return React.createElement(type, props);
  },
  createInputs: function(propList) {
    var fields = [];
    for(var props in propList ) {
      fields.push(this.createInput(propList[props]));
    }
    return fields;
  },
  createProgressBar: function() {
    return D.div({}, [
      D.div({
        style: {
          'marginTop': '20px'
        }
      }, "Your site is being built in the background..."),
      D.div({
        className: 'progress'
      }, D.div({
          className: "progress-bar progress-bar-striped active",
          role: "progressbar",
          'aria-valuenow': "100",
          'aria-valuemin': "0",
          'aria-valuemax': "100",
          style: {
            width: "100%"
          }
        }, D.span({
          className: "sr-only"
        }, "Building...")
      ))]
    );
  },
  createHeading: function(text) {
    var heading = '';
    var button = '';
    var skip = '';

    if( !this.state.complete ) {
      skip = this.createProgressBar();
    }

    if( this.state.phase > 1 ) {
      button = D.div({},
        skip
      );
    }

    if( text ) {
      heading = D.div({
        className: 'panel panel-info'
      },
        [
          D.div({
            className: 'panel-heading'
          },
            D.h3({
              className: 'panel-title'
            }, "Step " + this.state.phase)
          ),
          D.div({
            className: 'panel-body'
          }, [
            text,
            button
          ])
        ]
      );
    }

    return heading;
  },
  createMessage: function(){
    var messageDisplay = '';

    if(this.state.errors || this.state.message){

     var className = "alert ";
     var message = "";

     if( this.state.errors ) {
       className += "alert-danger";
       message = this.state.errors;
     }
     else{
       className += "alert-success";
       message = this.state.message;
     }
     messageDisplay = D.div({
        className: className,
        role: 'alert',
        key: 'message-output',
        ref: 'message'
      },
        [
          message,
          D.a({
            onClick: this.skipConfig
          }, "Skip configuration")
        ]
      );
    }

    return messageDisplay;
  },
  coreFields: function() {
    var fields = [
      {
        name: "site_id",
        validators: ['required'],
        labelText: "Site ID",
        formHelp: "The id of the site. This ends up as part of the URL. No special characters are allowed.",
      },
      {
        type: "select",
        name: "default_language",
        validators: ['required'],
        labelText: "Language",
        formHelp: "The main language of the site.",
        dataSet: this.props.initial.languages
      },
      {
        name: "portal_timezone",
        type: "select",
        labelText: "Timezone",
        formHelp: "The default timezone setting of the portal. Users will be able to set their own timezone, if available timezones are defined in the date and time settings.",
        dataSet: this.props.initial.timezones
      }
    ];

    if( this.state.advanced ) {
      var extras = [
        {
          name: "extension_ids",
          type: "fieldset",
          labelText: "Add-ons",
          formHelp: "Select any add-ons you want to activate immediately. You can also activate add-ons after the site has been created using the Add-ons control panel.",
          dataSet: this.props.initial.extensions,
          dataValues: appStore.get('extension_ids')
        }
      ];

      fields = fields.concat(extras);
    }

    return fields;
  },
  APIFields: function() {
    var apiFields = [
     {
       name: "castle.princexml_server_url",
       labelText: "PrinceXML Server Url",
       validators: ['url'],
       formHelp: "Required in order to convert documents",
     },
     {
       name: "castle.google_api_email",
       labelText: "Google API Email",
       validators: ['email'],
       type: 'email',
     },
     {
       name: "castle.google_analytics_id",
       labelText: "Google Analytics ID",
       formHelp: "for use with gathering content statistics",
     },
     {
       name: "castle.recaptcha_private_key",
       labelText: "Recaptcha Private Key",
     },
     {
       name: "castle.recaptcha_public_key",
       labelText: "Recaptcha Public Key",
     },
     {
       name: "castle.aws_s3_key",
       labelText: "AWS S3 Key",
     },
     {
       name: "castle.aws_s3_secret",
       labelText: "AWS S3 Secret",
     },
     {
       name: "castle.aws_s3_bucket",
       labelText: "AWS S3 Bucket",
     },
    ];

    return apiFields;
  },
  tabChange: function(e) {
    e.preventDefault();

    if( e.target.hasAttribute("disabled") ) {
      return;
    }

    if( this.checkFields() ) {
      var phase = $(e.target).data('phase');
      this.setState({
        phase: phase
      });
    }
  },
  checkFields: function() {
    for( var item in this.refs ) {

      if( !this.refs[item].state ||
          !this.refs[item].validateImmediately ||
          !this.refs[item].state.touched ) {
        continue;
      }

      var val = appStore.get(item);

      this.refs[item].validateImmediately(val);

      //We're checking each form item before switching tabs,
      //if anything is invalid, stop immediately
      if( this.refs[item].state.valid === false ) {
        return false;
      }
    }

    return true;
  },
  siteFields: function() {
    return [
      {
        name: "plone.site_title",
        validators: ['required'],
        labelText: "Site",
        formHelp: "A short title for the site. This will be shown in the title of the browser window on each page.",
      },
      {
        name: "plone.short_site_title",
        labelText: "Short site title",
        defaultValue: "Castle"
      },
      {
        name: "plone.site_logo",
        labelText: "Site Logo",
        formHelp: "This shows a custom Logo on your site. Leave blank to use the default CastleCMS logo.",
        type: "file",
        validators: ['image'],
        isImage: true
      },
      {
        name: "plone.public_url",
        labelText: "Public URL",
        formHelp: "The URL the public will use to view your site.",
        validators: ['url']
      },
      {
        name: "plone.backend_url",
        labelText: "Backend URL",
        formHelp: "The URL from which you will be editing and maintaing site content.",
        validators: ['url']
      },
      {
        name: "plone.disable_contact_form",
        labelText: "Disable contact form",
        type: "checkbox",
        checked: false
      }
    ];
  },
  socialMediaFields: function() {
    return [
      {
        name: "plone.share_social_data",
        labelText: "Share social data",
        formHelp: "Include meta tags on pages to give hints to social media on how to render your pages better when shared",
        type: "checkbox",
        checked: true
      },
      {
        name: "plone.twitter_username",
        labelText: "Twitter username",
        formHelp: "To identify things like Twitter Cards",
      },
      {
        name: "plone.facebook_app_id",
        labelText: "Facebook app ID",
        formHelp: "To be used with some integrations like open graph data"
      },
      {
        name: "plone.facebook_username",
        labelText: 'Facebook username',
        formHelp: "For linking open graph data to a facebook account"
      },
      {
        name: "plone.twitter_consumer_key",
        labelText: "Twitter consumer key"
      },
      {
        name: "plone.twitter_consumer_secret",
        labelText: "Twitter consumer secret"
      }
    ];
  },
  render: function() {
    var fields = null;
    var heading = '';
    if( this.state.phase == 1 ) {
      heading = "Let's get the basics taken care of. Then we can start building your site in the background.";
      fields = this.coreFields();
    }
    else if( this.state.phase == 2 ) {
      heading = "Let's configure some general, site-wide settings";
      fields = this.siteFields();
    }
    else if( this.state.phase == 3 ) {
      heading = "CastleCMS can leverage several social media sites to publish your content.";
      fields = this.socialMediaFields();
    }
    else if( this.state.phase == 4 ) {
      heading = "Now let's setup some of the APIs that CastleCMS uses.";
      fields = this.APIFields();
    }

    var message = this.createMessage();
    heading = this.createHeading(heading);
    var tabs = this.createTabs();
    var inputs = this.createInputs(fields);
    var buttons = this.createButtons();

    var form = D.form({
     key: "setup",
     ref: "setup",
     onChange: this._onChange
    },
    [
     message,
     heading,
     tabs,
     inputs,
     buttons
    ]);

    return form;
  },
  submitConfigurations: function(e) {
    e.preventDefault();
    var self = this;

    var data = appStore.getAll();

    var coreFields = this.coreFields();
    coreFields = coreFields.map(function(v) {
      return v.name;
    });

    //More complex values, such as images, use objects
    //to store data instead of just single values
    for( var item in data ) {

      if(!data[item] || coreFields.indexOf(item) > 0 ) { continue; }
      data[item] = data[item].output || data[item];
    }

    var url = window.location.origin + '/' + appStore.get('site_id') + '/@@set-config';

    $.ajax({
      url: url,
      context: self,
      data: data,
      dataType: 'json',
      method: 'POST'
    }).done(function(res) {
      if( res.success ) {
        window.location.replace(res.start);
      }else{
        this.setState({
          'errors': res.errors
        });
      }
    });
  },
  submitInitialForm: function(e) {
   e.preventDefault();
   var self = this;

   //Pull the data from the store, and
   //reformat the extensions to be more
   //useful on the other end.
   var data = appStore.getAll();
   var extensions = this.exportExtensions();
   data.extension_ids = extensions;

   var url = self.props.initial.action_url;

   data.submitted = true;
   $.ajax({
     url: url,
     context: self,
     data: data,
     dataType: 'json',
     method: 'POST'
   }).done(function(res) {
     if( res.success === false ) {

       //Set submitted to false so we can safely resubmit
       this.setState({
         'errors': res.msg,
         'submitted': false,
         'phase': 1
       });
     }else{
       this.setState({
         'message': 'Your site was created successfully!',
         'submitted': false,
         complete: true,
         url: res.url
       });
     }
   }).fail(function(res) {
     alert("Something went wrong while trying to create your site.");
   });

   this.setState({
     'phase': this.state.phase + 1,
     'submitted': true,
     'errors': null,
     'message': null
   });
 },
 toggleAdvanced: function(e) {
   e.preventDefault();

   if( this.state.advanced ) {
     this.setState({
       advanced: 0
     });
   }else{
     this.setState({
       advanced: 1
     });
   }
 }
});

React.render(
  React.createElement(siteSetup, {"initial": JSON.parse(document.getElementById("form_data").innerHTML)}),
  document.getElementById("reactForm")
);

});
