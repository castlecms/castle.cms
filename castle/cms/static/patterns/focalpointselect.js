/* global define, mOxie */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'castle-url/components/image-focal-point-selector',
  'mockup-utils',
  'castle-url/libs/moxie/bin/js/moxie'
], function($, Base, _, R, FocalPointSelector, utils) {
  'use strict';

  var D = R.DOM;

  var FocalPointSelectorComponent = R.createClass({

    getInitialState: function(){
      return {
        loading: false,
        focal_point: this.props.focal_point,
        image: null,
        previewImage: null,
        previewWidth: '',
        previewHeight: '',
        previewUrl: '',
        hidden: true
      };
    },

    getDefaultProps: function(){
      return {
        focal_point: [0, 0],
        reference: null
      };
    },

    loadImage: function(asset){
      var that = this;
      that.setState({
        loading: true
      });
      that.state.image = new mOxie.Image();
      utils.loading.show();
      that.state.image.onload = function() {
        // make a new image object for the downsize
        that.props.width = that.state.image.width;
        that.props.height = that.state.image.height;
        if(that.props.focal_point[0] > that.state.image.width ||
           that.props.focal_point[0] === 0){
          that.props.focal_point[0] = that.state.image.width / 2;
        }
        if(that.props.focal_point[1] > that.state.image.height ||
           that.props.focal_point[1] === 0){
          that.props.focal_point[1] = that.state.image.height / 2;
        }
        that.props.exists = true;

        var blob = that.state.image.getAsBlob();
        var resizedImg = new mOxie.Image();
        resizedImg.onload = function(){
          resizedImg.onresize = function(){
            utils.loading.hide();
            that.setState({
              previewUrl: resizedImg.getAsDataURL('image/png'),
              previewWidth: resizedImg.width,
              previewHeight: resizedImg.height,
              loading: false,
              previewImage: resizedImg
            });
          };
          resizedImg.downsize({width: 300});
        };
        resizedImg.load(blob);
      };
      that.state.image.onerror = function(){
        utils.loading.hide();
        that.props.exists = false;
        that.setState({
          loading: false
        });
      };
      that.state.image.load(asset);
    },

    render: function(){
      var that = this;
      if(that.state.hidden){
        return D.div({});
      }
      if(that.state.loading){
        return D.div({}, 'Loading image...');
      }
      if(!that.props.exists){
        return D.div({}, 'No image selected');
      }
      return D.div({ className: 'imagewidget-image-container'}, [
        R.createElement(FocalPointSelector, {
          url: that.state.previewUrl,
          width: that.state.previewWidth,
          fullWidth: that.props.width,
          height: that.state.previewHeight,
          fullHeight: that.props.height,
          focalPoint: that.props.focal_point,
          pointerOffsetY: -6,
          onFocalSet: function(focal_point){
            that.props.focal_point = focal_point;
            that.setState({
              dirty: true
            });
            that.props.onSelected(focal_point);
          }
        })
      ]);
    },
  });

  var FocalPointSelectPattern = Base.extend({
    name: 'focalpointselect',
    trigger: '.pat-focalpointselect',
    defaults: {
    },
    init: function() {
      var self = this;
      self.$el.attr('type', 'hidden');
      var $form = self.$el.closest('form');

      var $relatedItems = $('.pat-relateditems', $form);
      var $displayType = $('[id*="-display_type"].field', $form);
      var $parent = self.$el.parent();

      var focal_point_val = self.$el.val();
      var focal_point;
      if(focal_point_val){
        focal_point = JSON.parse(focal_point_val);
      }else{
        focal_point = [0,0];
      }

      var $checkboxContainer = $('<div class="checkbox"><label><input type="checkbox"> Override focal point for selected image</label></div>');
      var $checkbox = $('input', $checkboxContainer);
      $parent.append($checkboxContainer);

      var el = document.createElement('div');
      $parent.append(el);

      self.component = R.render(R.createElement(FocalPointSelectorComponent, {
        onSelected: function(fp){
          self.$el.val(JSON.stringify(fp));
        },
        focal_point: focal_point
      }), el);

      var portalUrl = $('body').attr('data-portal-url');
      $relatedItems.on('change', function(e){
        if(e.target.value){
          self.component.loadImage(portalUrl + '/resolveuid/' + e.target.value + '/@@images/image?_=' + utils.generateId());
        }else{
          self.component.setState({
            exists: false
          });
        }
      });

      var uid = $relatedItems.val();
      if(uid){
        self.component.loadImage(portalUrl + '/resolveuid/' + uid + '/@@images/image?_=' + utils.generateId());
      }

      if(focal_point_val){
        $checkbox[0].checked = true;
        self.component.setState({
          hidden: false
        });
      }else{
        self.component.setState({
          hidden: true
        });
      }

      $checkbox.on('change', function(e){
        if(e.target.checked){
          self.component.setState({
            hidden: false
          });
        }else{
          self.component.setState({
            hidden: true
          });
          self.$el.attr('value', '');
        }
      });

      // if there is a display type, we are not even showing this field if natural is selected
      if($displayType.size() > 0){
        var val = $('select', $displayType).val();
        if(!val || val === 'natural' || val === 'fullwidth'){
          $parent.hide();
        }
        $('select', $displayType).on('change', function(e){
          var val = e.target.value;
          if(!val || val === 'natural' || val === 'fullwidth'){
            $parent.hide();
          }else{
            $parent.show();
          }
        });
      }
    }
  });

  return FocalPointSelectPattern;

});
