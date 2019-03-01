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

  var QualityCheckWrapper = R.createClass({
    // for being able to toggle open and closed
    getInitialState: function(){
      return {
        checked: false,
        open: false,
        valid: false
      };
    },
    getDefaultProps: function(){
      return {
        onQACheck: function(){}
      };
    },
    onChecked: function(){
      if(this.refs.qa){
        var valid = this.refs.qa.isValid();
        this.setState({
          checked: true,
          open: !valid,
          valid: valid
        });
        this.props.onQACheck(valid);
      }
    },
    onToggleClicked: function(e){
      e.preventDefault();
      this.setState({
        open: !this.state.open
      });
    },
    render: function(){
      var qa = R.createElement(QualityCheck, {
        delay: true, onFinished: this.onChecked, ref: 'qa' });
      var toggleText = 'Show Quality Check';
      if(this.state.open){
        toggleText = 'Hide Quality Check';
      }
      var btnIconClass = '';
      var btnClass = 'plone-btn plone-btn-warning';
      if(this.state.valid){
        //btnIconClass = 'glyphicon glyphicon-ok';
        btnClass = 'plone-btn plone-btn-default';
      }
      return D.div({className: 'quality-check-wrapper'}, [
        D.button({ className: btnClass,
                   onClick: this.onToggleClicked}, [
          D.span({ className: btnIconClass}),
          toggleText
        ]),
        D.div({ style: {display: this.state.open && 'block' || 'none'}}, [
          qa
        ])
      ]);
    }
  });

  var WorkflowModalComponent = cutils.Class([Modal], {
    getInitialState: function(){
      return {
        transition: '',
        comment: '',
        qaValid: false
      };
    },

    transitionClicked: function(e){
      var data = {
        transition: e.target.value
      };
      // set early here..
      this.state.transition = e.target.value;
      if(this.isQARequired()){
         if(this.state.comment.length === 0){
           data.comment = 'OVERRIDE: ';
         }else if(this.state.comment.indexOf('OVERRIDE:') === -1){
            data.comment = 'OVERRIDE: ' + this.state.comment;
         }
      }else{
        if(this.state.comment.trim() === 'OVERRIDE:'){
          // we can remove now
          data.comment = '';
        }
      }
      this.setState(data);
    },

    commentChanged: function(e){
      var data = {
        comment: e.target.value
      };
      if(this.isQARequired()){
        if(data.comment.indexOf('OVERRIDE:') === -1){
          return; // do not allow edit. They can *not* edit "OVERRIDE:" out
        }
      }
      this.setState(data);
    },

    qaDone: function(valid){
      this.setState({
        qaValid: valid
      });
    },

    renderContent: function(){
      var that = this;
      var transitionComps = [D.div({ className: 'radio'}, D.label({}, [
        D.input({ type: 'radio', value: '',
                  name: 'transition',
                  checked: that.state.transition === '',
                  onClick: that.transitionClicked}),
        'No change'
      ]))];

      transitionComps = transitionComps.concat(
        that.props.workflow.transitions.map(function(transition){
          return D.div({ className: 'radio'}, D.label({}, [
            D.input({ type: 'radio', value: transition.id,
                      name: 'transition',
                      checked: that.state.transition === transition.id,
                      onClick: that.transitionClicked}),
            transition.title
          ]));
        }));

      var commentClassName = 'form-group ';
      if(this.isQARequired()){
        commentClassName += 'has-error';
      }
      return D.div({ className: 'castle-preview form-horizontal'}, [
        R.createElement(QualityCheckWrapper, {delay: false, ref: 'qa',
                                              onQACheck: this.qaDone }),
        D.hr({}),
        D.div({className: 'form-group'}, [
          D.label({ htmlFor: '' }, 'Change state'),
          D.div({ className: 'formHelp'}, "Select the transition to be used for modifying the item's state."),
          transitionComps
        ]),
        D.div({className: commentClassName}, [
          D.label({}, 'Comment'),
          D.div({ className: 'formHelp'}, 'Comments will be added to the publishing history. ' +
                                          'Comments are required when quality check does not pass and you are attempting to publish.'),
          D.textarea({ className: 'form-control', value: that.state.comment,
                       onChange: that.commentChanged})
        ])
      ]);
    },

    onChangeClicked: function(e){
      e.preventDefault();
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-base-url') + '/@@content-workflow',
        data: {
          _authenticator: utils.getAuthenticator(),
          transition_id: this.state.transition,
          comment: this.state.comment,
          action: 'transition'
        }
      }).always(function(){
        utils.loading.hide();
      }).fail(function(){
        alert('Error performing transition');
      }).done(function(){
        window.location.reload();
      });
      this.hide();
    },

    isQARequired: function(){
      return (!this.state.qaValid &&
              this.state.transition === 'publish' &&
              this.props.workflow.publishRequireQualityCheck);
    },

    renderFooter: function(){
      var buttons = [
        D.button({ type: 'button', className: 'plone-btn plone-btn-default', 'data-dismiss': 'modal'}, 'Cancel'),
        D.button({
          type: 'button', className: 'plone-btn plone-btn-primary pull-right',
          disabled: (this.isQARequired() &&
                     this.state.comment.trim().length <= 'OVERRIDE:'.length) ||
                    !this.state.transition,
          onClick: this.onChangeClicked}, 'Change')
      ];
      return D.div({ className: 'btn-container'}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'workflow-content-modal',
        title: 'Publishing Process',
        workflow: {}
      });
    }
  });

  return WorkflowModalComponent;
});
