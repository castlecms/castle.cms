/* global mOxie */

define([
  'jquery',
  'pat-base',
  'castle-url/libs/react/react.min',
  'castle-url/components/image-focal-point-selector',
  'castle-url/components/image-editor',
  'castle-url/components/utils',
  'mockup-utils',
  'mockup-patterns-relateditems',
  'castle-url/libs/moxie/bin/js/moxie'
], function($, Base, R, FocalPointSelector, ImageEditor, cutils, utils, RelatedItems) {
  "use strict";

  var D = R.DOM;

  var ImageWidgetComponent = R.createClass({

    getInitialState: function(){
      return {
        dragging: false,
        dirty: false,
        remove: false,
        imageDirty: false,
        loading: true,
        showEditor: false,
        focal_point: this.props.focal_point,
        image: null,
        previewImage: null,
        previewWidth: '',
        previewHeight: '',
        previewUrl: '',
        selectReference: this.props.reference !== null
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
      that.state.image = new mOxie.Image();
      utils.loading.show();
      that.state.image.onload = function() {
        // make a new image object for the downsize
        that.props.width = that.state.image.width;
        that.props.height = that.state.image.height;
        if(!that.props.focal_point){
          that.props.focal_point = [0, 0];
        }
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

    componentDidMount: function(){
      var that = this;
      if(that.props.exists){
        that.loadImage(that.props.download_url);
      }else{
        that.setState({
          loading: false
        });
      }

      var accept = [
        {title: "Images", extensions: "jpg,gif,png"}
      ];

      var portalUrl = $('body').attr('data-portal-url');
      mOxie.Env.swf_url = portalUrl + '/++plone++castle/libs/moxie/bin/flash/Moxie.min.swf';
      mOxie.Env.xap_url = portalUrl + '/++plone++castle/libs/moxie/bin/silverlight/Moxie.min.xap';

      var fileInput = new mOxie.FileInput({
        browse_button: that.refs.upload_btn.getDOMNode(),
        runtime_order: 'html5,flash,html4',
        multiple: false,
        accept: accept
      });

      var handlFileAdded = function(image){
        that.props.filename = image.name;
        that.setState({
          dirty: true,
          imageDirty: true,
          loading: true,
          remove: false
        }, function(){
          if(image.type === 'image/gif'){
            // need to convert it first
            that.loadGif(image);
          }else{
            that.loadImage(image);
          }
        });
      };

      fileInput.onchange = function(e) {
        handlFileAdded(e.target.files[0]);
      };

      fileInput.init(); // initialize

      var dropEl = that.refs.droparea.getDOMNode();
      var fileDrop = new mOxie.FileDrop({
        drop_zone: dropEl,
        accept: accept
      });

      fileDrop.ondrop = function() {
        var dz = this;
        handlFileAdded(dz.files[0]);
        dropEl.style.background = '';
      };
      fileDrop.ondragenter = function(){
        that.setState({
          dragging: true
        });
      };
      fileDrop.ondragleave = function(){
        that.setState({
          dragging: false
        });
      };

      fileDrop.init();

      /* setup related items */
      var selection = [];
      if(this.props.reference){
        selection = [this.props.reference];
      }
      var $re = $(that.refs.relateditem.getDOMNode());
      try {
        var options = JSON.parse($('.pat-relateditems').attr('data-pat-relateditems'));
      } catch (e) {
        var options = {};
      }
      var pattern = new RelatedItems($re, cutils.extend(options, {
        vocabularyUrl: $('body').attr('data-portal-url') + '/@@getVocabulary?name=plone.app.vocabularies.Catalog',
        maximumSelectionSize: 1,
        multiple: false,
        allowAdd: false,
        noItemsSelectedText: 'No image selected',
        initial_selection: selection,
        selectableTypes: ['Image'],
        baseCriteria: [{
          i: 'portal_type',
          o: 'plone.app.querystring.operation.selection.any',
          v: ['Image', 'Folder']
        }]
      }));
      $re.on('change', function(){
        if(pattern.component.state.selected.length > 0){
          that.props.reference = pattern.component.state.selected[0];
        }else{
          that.props.reference = null;
        }
      });
    },

    loadGif: function(image){
      var that = this;
      utils.loading.show();
      var xhr = new mOxie.XMLHttpRequest();
      var fd = new mOxie.FormData();
      xhr.open('post', $('body').attr('data-base-url') + '/@@convert-to-png');
      fd.append('data', image.slice());
      xhr.onload = function() {
        if (xhr.response) {
          that.loadImage('data:image/png;base64,' + xhr.response);
        }else{
          alert('error converting image');
        }
        utils.loading.hide();
      };
      xhr.bind('error runtimeerror', function() {
        utils.loading.hide();
        alert('error converting image');
      });

      xhr.send(fd, {
        runtime_order: 'html5,flash,html4',
        required_caps: {
          send_multipart: true
        }
      });
    },

    renderImage: function(){
      var that = this;
      if(that.state.loading){
        return D.div({}, 'Loading image...');
      }
      if(!that.props.exists){
        return D.div({}, 'No image');
      }
      return D.div({ className: 'imagewidget-image-container'}, [
        R.createElement(FocalPointSelector, {
          url: that.state.previewUrl,
          width: that.state.previewWidth,
          fullWidth: that.props.width,
          height: that.state.previewHeight,
          fullHeight: that.props.height,
          focalPoint: that.props.focal_point,
          onFocalSet: function(focal_point){
            that.props.focal_point = focal_point;
            that.setState({
              dirty: true
            });
          }
        }),
        D.p({ className: 'discreet'}, 'Filename: ' + that.props.filename)
      ]);
    },

    renderUploader: function(){
      var that = this;
      var style = {};
      if(that.state.loading || that.state.showEditor){
        style = { display: 'none'};
      }
      return D.div({ ref: 'droparea', className: 'droparea', style: style }, [
        'Drop here to replace image or ',
        D.button({ ref: 'upload_btn', className: 'btn btn-default castle-btn-select-files' }, 'Select an image'),
      ]);
    },

    render: function(){
      var that = this;
      var left = [];
      var buttons = [];
      var right = [
        that.renderUploader()
      ];

      if(that.state.dirty){
        buttons.push(D.button({ className: 'plone-btn plone-btn-default',
                                onClick: function(e){
                                  e.preventDefault();
                                  that.props.focal_point = that.props.original_focal_point;
                                  that.setState({
                                    dirty: false,
                                    imageDirty: false,
                                    loading: true,
                                    remove: false
                                  }, function(){
                                    that.loadImage(that.props.download_url);
                                  });
                                }}, 'Cancel changes'));
      }

      if(that.props.exists && !that.state.remove){
        left.push(that.renderImage());
        if(!that.props.required){
          buttons.push(D.button({ className: 'plone-btn plone-btn-default',
                                  onClick: function(e){
                                    e.preventDefault();
                                    that.setState({
                                      remove: true,
                                      dirty: true
                                    });
                                  }}, 'Remove image'));
        }

        if(!that.state.loading && !that.state.remove){
          if(that.state.showEditor){
            right.push(R.createElement(ImageEditor, {
              key: 'image-editor',
              file: that.state.image,
              onSave: function(blob){
                that.setState({
                  showEditor: false,
                  loading: true,
                  dirty: true,
                  imageDirty: true
                }, function(){
                  that.loadImage(blob);
                });
              },
              onCancel: function(){
                that.setState({
                  showEditor: false
                });
              }}));
          }else{
            buttons.push(D.button({
              className: "plone-btn plone-btn-default castle-btn-edit",
              onClick: function(e){
                e.preventDefault();
                that.setState({
                  showEditor: true
                });
              }}, 'Edit Image'));
          }
        }
      }

      var leftClass = 'col-md-5';
      var rightClass = 'col-md-7';
      if(left.length === 0){
        leftClass = '';
        rightClass = 'col-md-12';
      }

      return D.div({ className: 'castle-imagewidget-container'}, [
        D.div({ style: that.state.selectReference && { display: 'none'} || {}}, [
          D.div({ className: 'row'}, [
            D.div({ className: leftClass }, left),
            D.div({ className: rightClass}, [
              right
            ])
          ]),
          D.div({ className: 'btn-container'}, buttons)
        ]),
        D.div({ style: !that.state.selectReference && { display: 'none'} || {}}, [
          D.input({ ref: 'relateditem', type: 'hidden' })
        ]),
        D.div({ className: 'form-group'},
          D.label({}, [
            D.input({ type: 'checkbox', checked: that.state.selectReference, onClick: function(){
              that.setState({
                selectReference: !that.state.selectReference
              });
            }}),
            'Or, select image from site to use as the lead image'
          ])
        )
      ]);
    }
  });

  var ImageWidget = Base.extend({
    name: 'imagewidget',
    trigger: '.pat-imagewidget',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var that = this;
      that.$action = that.$el.siblings('.imagewidget-action');
      var options = cutils.extend(that.options, {
        original_focal_point: that.options.focal_point
      });
      that.component = R.render(R.createElement(ImageWidgetComponent, options), that.$el[0]);

      that.$el.closest('form').on('submit', function(){
        if(that.component.state.selectReference){
          if(that.component.props.reference){
            that.$action.val('');
            that.addReference();
          } else {
            that.$action.val('nochange');
          }
        } else if(that.component.state.remove){
          that.$action.val('remove');
        }else if(!that.component.state.dirty){
          that.$action.val('nochange');
        }else{
          // add image data
          if(that.component.state.imageDirty){
            that.$action.val('');
            var data = document.createElement('input');
            data.type = 'hidden';
            data.name = that.options.name;
            data.value = that.component.state.image.getAsDataURL(that.component.state.image.type, 100);
            $(data).insertAfter(that.$el);

            var filename = document.createElement('input');
            filename.type = 'hidden';
            filename.name = that.options.name + '.filename';
            filename.value = that.component.props.filename;
            $(filename).insertAfter(that.$el);
          } else {
            that.$action.val('nochange');
          }

          // then add focal point data
          var focalX = document.createElement('input');
          focalX.type = 'hidden';
          focalX.name = that.options.name + '.focalX';
          focalX.value = that.component.props.focal_point[0];
          $(focalX).insertAfter(that.$el);

          var focalY = document.createElement('input');
          focalY.type = 'hidden';
          focalY.name = that.options.name + '.focalY';
          focalY.value = that.component.props.focal_point[1];
          $(focalY).insertAfter(that.$el);
        }
      });
    },
    addReference: function(){
      var that = this;
      var reference = document.createElement('input');
      reference.type = 'hidden';
      reference.name = that.options.name;
      if(that.component.state.selectReference){
        reference.value = 'reference:' + that.component.props.reference;
      } else {
        reference.value = '';
        that.$action.val('nochange');
      }
      $(reference).insertAfter(that.$el);
    }
  });

  return ImageWidget;

});
