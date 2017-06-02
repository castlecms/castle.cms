/* global history */

var HasHistory = !!window.history;


/* history version view code */
require([
'jquery',
'mockup-utils',
'pat-registry'
], function($, utils, Registry){

  var load = function(url){
    utils.loading.show();
    $.ajax({
      url: url
    }).done(function(data){
      var body = utils.parseBodyTag(data);
      var $dom = $(body);
      var $newContent = $('.history-content-wrapping', $dom);
      $('.history-content-wrapping').replaceWith($newContent);
      $('.history-info-container').replaceWith($('.history-info-container', $dom));

      Registry.scan($newContent);
      Registry.scan($('.history-info-container'));
      bind();
      if(HasHistory){
        history.pushState({}, "", url);
      }
    }).fail(function(){
      alert('error getting version');
    }).always(function(){
      utils.loading.hide();
    });
  };

  var bind = function(){
    $('.version-selector').on('change', function(e){
      e.preventDefault();
      var versionId = $(this).val();
      var url = window.location.origin + window.location.pathname + '?version=' + versionId;
      load(url);
    });
  };

  $(document).ready(function(){
    bind();
  });

  if(HasHistory){
    window.onpopstate = function(){
      load(window.location.href);
    };
  }
});

/* confirm revert to revision */
require([
  'jquery',
  'mockup-utils',
  'castle-url/components/utils',
  'castle-url/components/confirm',
  'moment'
], function($, utils, cutils, ConfirmationModalComponent, moment){
  var confirmed = false;
  $('.revert-form').submit(function(e){
    if(confirmed){
      // calling submit() gets us back here, short out if we are already confirmed
      // and execute the form action
      return;
    }

    var $form = $(this);
    e.preventDefault();
    cutils.createModalComponent(ConfirmationModalComponent, 'castle-confirmation-modal', {
      title: 'Confirm reverting to revision ' + $('[name="version_id"]', $form).val(),
      msg: 'Are you sure you want to revert to this revision which was last modified by "' +
        $form.attr('data-who') + '" on ' +
        moment($form.attr('data-when')).local().format('LLLL') + '?',
      onConfirm: function(){
        confirmed = true;
        $form.submit();
      }
    });
  });
});


/* update comments */
require([
  'jquery',
  'mockup-utils',
  'castle-url/components/utils',
  'castle-url/components/modal',
  'castle-url/libs/react/react.min',
], function($, utils, cutils, Modal, R){

  var D = R.DOM;

  var ChangeNoteModalComponent = cutils.Class([Modal], { // jshint ignore:line
    getInitialState: function(){
      return {
        comments: this.props.changeNote
      };
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'preview-content-modal',
        title: 'Update comments',
        comments: '',
        versionId: ''
      });
    },
    renderContent: function(){
      var that = this;
      return D.div({className: "form-group"}, [
        D.label({ htmlFor: "updateComments"}, 'Comments'),
        D.input({ type: "text", className: "form-control",
                  id: "updateComments", placeholder: "Comments",
                  value: that.state.comments,
                  onChange: function(e){
                    that.setState({
                      comments: e.target.value
                    });
                  }
                })
      ]);
    },
    renderFooter: function(){
      var that = this;
      var buttons = [];
      buttons.push(D.button({ className: 'plone-btn plone-btn-default',
                              onClick: this.hide }, 'Cancel'));
      buttons.push(D.button({ className: 'plone-btn plone-btn-warning',
                              onClick: that.submit }, 'Change'));
      return D.div({}, buttons);
    },
    submit: function(e){
      utils.loading.show();
      var that = this;
      e.preventDefault();
      $.ajax({
        url: $('body').attr('data-base-url') + '/@@update-change-comment',
        method: 'POST',
        data: {
          _authenticator: utils.getAuthenticator(),
          version_id: that.props.versionId,
          comments: that.state.comments
        }
      }).done(function(data){
        if(data.success){
          var existing = $('#rendered-comments-' + that.props.versionId);
          if(existing.size() > 0){
            existing.html(that.state.comments);
          }else{
            window.location.reload();
          }
        }else{
          alert('Error saving comment: ' + data.error);
        }
      }).fail(function(){
        alert('error saving updated comments');
      }).always(function(){
        utils.loading.hide();
        that.hide();
      });
    }
  });

  $('.btn-modify-comments').off('click').on('click', function(e){
    e.preventDefault();
    cutils.createModalComponent(ChangeNoteModalComponent, 'castle-comments-modal', {
      versionId: $(this).attr('data-version-id'),
      changeNote: $(this).attr('data-comments')
    });
  });
});
