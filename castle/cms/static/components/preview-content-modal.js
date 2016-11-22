/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/modal',
  'castle-url/components/utils'
], function($, Base, _, R, utils, Modal, cutils) {
  'use strict';
  var D = R.DOM;

  var PreviewModalComponent = cutils.Class([Modal], {
    getInitialState: function(){
      return {
        size: 'full'
      };
    },
    componentDidMount: function(){
      utils.loading.show();
      var that = this;
      Modal.componentDidMount.apply(this);
      // calc height as it is loading

      var setHeight = function(){
        var $iframe = $(that.refs.iframe.getDOMNode());
        var newHeight = 0;
        $iframe.contents().find('body > *').each(function(){
          newHeight += $(this).height();
        });
        if(newHeight > $iframe.height()){
          $iframe.height(newHeight);
          utils.loading.hide();
        }
        that.props.timeout = setTimeout(setHeight, 500);
      };
      that.props.timeout = setTimeout(setHeight, 500);
    },
    componentWillUnmount: function(){
      clearTimeout(this.props.timeout);
    },
    componentDidUpdate: function(){
      clearTimeout(this.props.timeout);
      this.componentDidMount();
    },
    sizeChanged: function(e){
      var val = e.target.value;
      if(val === 'full'){
        this.props.width = null;
      }else if(val === 'phone'){
        this.props.width = '500px';
      }else if(val === 'phablet'){
        this.props.width = '680px';
      }else if(val === 'tablet'){
        this.props.width = '800px';
      }
      this.setState({
        size: val
      });
    },
    renderContent: function(){
      var that = this;
      return D.div({ className: 'castle-preview form-horizontal'}, [
        D.div({ className: 'form-group'}, [
          D.label({ className: 'col-sm-4 control-label'}, 'Select device size'),
          D.div({ className: "col-sm-6" },
            D.select({value: that.state.size, onChange: that.sizeChanged, className: 'form-control'}, [
              D.option({value: 'full'}, 'Full Size'),
              D.option({value: 'tablet'}, 'Tablet'),
              D.option({value: 'phablet'}, 'Phablet'),
              D.option({value: 'phone'}, 'Phone')
            ])
          )
        ]),
        D.iframe({ src: $('body').attr('data-view-url') + '?VIEW_AS_ANONYMOUS_VIEW=true',
                   width: '100%', ref: 'iframe', key: this.props.width})
      ]);
    },
    renderFooter: function(){
      var buttons = [D.button({ type: 'button', className: 'plone-btn plone-btn-primary',
                                'data-dismiss': 'modal'}, 'Done')];
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'preview-content-modal',
        title: 'Preview content',
        timeout: 0
      });
    }
  });

  return PreviewModalComponent;
});
