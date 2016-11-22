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
        url: null,
        width: '',
        fullWidth: '',
        height: '',
        fullHeight: '',
        focalPoint: [0, 0],
        pointerOffsetX: 12,
        pointerOffsetY: 6,
        onFocalSet: function(){}
      };
    },

    previewClicked: function(e){
      var offset = $(this.refs.previewImage.getDOMNode()).offset();
      this.props.onFocalSet([
        (e.pageX - offset.left) / (this.props.width / this.props.fullWidth),
        (e.pageY - offset.top) / (this.props.height / this.props.fullHeight),
      ]);
    },

    render: function(){
      var centerPoint = '';

      if(this.props.enabled){
        centerPoint = D.div({
          className: 'focalpoint-image-center',
          style: {
            left: ((this.props.width / this.props.fullWidth) * this.props.focalPoint[0]) - this.props.pointerOffsetX,
            top: ((this.props.height / this.props.fullHeight) * this.props.focalPoint[1]) + this.props.pointerOffsetY
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
