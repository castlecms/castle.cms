define([
  'jquery',
  'castle-url/libs/react/react.min'
], function($, R) {
  'use strict';
  var D = R.DOM;

  var FocalPointSelector = R.createClass({
    getDefaultProps: function(){
      return {
        enabled: true,
        readOnly: false,
        url: null,
        width: '',
        fullWidth: '',
        height: '',
        fullHeight: '',
        focalPoint: [0, 0],
        pointerOffsetX: 12,
        pointerOffsetY: 12,
        onFocalSet: function(){}
      };
    },

    previewClicked: function(e){
      var offset = $(this.refs.previewImage.getDOMNode()).offset();
      var fpX = (e.pageX - offset.left) / (this.props.width / this.props.fullWidth);
      fpX = Math.min(this.props.fullWidth,  Math.max(fpX,0));
      var fpY = (e.pageY - offset.top) / (this.props.height / this.props.fullHeight);
      fpY = Math.min(this.props.fullHeight,  Math.max(fpY,0));
      this.props.onFocalSet([fpX, fpY]);
    },

    render: function(){
      var centerPoint = '';

      if(this.props.enabled){
        centerPoint = D.div({
          className: 'focalpoint-image-center'+(this.props.readOnly?' focalpoint-disabled':''),
          style: {
            left: ((this.props.width / this.props.fullWidth) * this.props.focalPoint[0]) - this.props.pointerOffsetX,
            top: ((this.props.height / this.props.fullHeight) * this.props.focalPoint[1]) - this.props.pointerOffsetY
          } });
      }
      return D.div({ className: 'focalpoint-image-container', onClick: this.previewClicked }, [
        centerPoint,
        D.img({ src: this.props.url, ref: 'previewImage'})
      ]);
    }
  });

  return FocalPointSelector;
});
