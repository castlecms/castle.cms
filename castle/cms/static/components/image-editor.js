/* global mOxie */

define([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/libs/cropper/dist/cropper.min'
], function($, R, utils) {
  'use strict';
  var D = R.DOM;

  var Cropper = R.createClass({
    componentDidMount: function(){
      $(this.refs.img.getDOMNode()).cropper(this.props.cropperOptions);
    },
    render: function(){
      return D.img({src: this.props.image, ref: 'img'});
    },
    getDefaultProps: function(){
      return {
        cropperOptions: {
          zoomOnWheel: false
        }
      };
    }
  });

  var CropperContainer = R.createClass({
    getInitialState: function(){
      return {
        image: null
      };
    },
    componentDidMount: function(){
      var that = this;
      var img = new mOxie.Image();
      utils.loading.show();
      img.onload = function() {
        utils.loading.hide();
        that.setState({
          image: img.getAsDataURL('image/png')
        });
      };
      img.load(that.props.file);
    },
    cancelClicked: function(e){
      e.preventDefault();
      this.props.onCancel();
    },
    saveClicked: function(e){
      var that = this;
      e.preventDefault();
      utils.loading.show();
      var canvas = $(this.refs.cropper.refs.img.getDOMNode()).cropper('getCroppedCanvas');
      var dataUrl = canvas.toDataURL();
      var img = new mOxie.Image();
      img.onload = function() {
        utils.loading.hide();
        var blob = img.getAsBlob('image/png');
        that.props.onSave(blob, img);
      };
      img.load(dataUrl);
    },
    rotateLeft: function(e){
      e.preventDefault();
      $(this.refs.cropper.refs.img.getDOMNode()).cropper('rotate', -90);
    },
    rotateRight: function(e){
      e.preventDefault();
      $(this.refs.cropper.refs.img.getDOMNode()).cropper('rotate', 90);
    },
    render: function(){
      var img = '';
      if(this.state.image){
        img = R.createElement(Cropper, { image: this.state.image, ref: 'cropper'});
      }
      return D.div({ className: 'castle-cropper-container', ref: 'container'}, [
        img,
        D.div({ className: 'plone-btn-group'}, [

          D.button({ className: 'plone-btn plone-btn-default castle-btn-rotate-left', onClick: this.rotateLeft}, 'Rotate Left'),
          D.button({ className: 'plone-btn plone-btn-default castle-btn-rotate-right', onClick: this.rotateRight}, 'Rotate Right'),
          D.button({ className: 'plone-btn plone-btn-default castle-btn-cancel', onClick: this.cancelClicked}, 'Cancel'),
          D.button({ className: 'plone-btn plone-btn-default castle-btn-save', onClick: this.saveClicked}, 'Save')
        ])
      ]);
    },
    getDefaultProps: function(){
      return {
        onCancel: function(){},
        onSave: function(){}
      };
    }
  });

  return CropperContainer;
});
