/* global define, alert, mOxie */
/*jshint quotmark: false */

define([
  'jquery',
  'castle-url/libs/react/react.min',
  'castle-url/components/utils',
  'mockup-utils',
  'castle-url/components/image-editor',
  'castle-url/components/image-focal-point-selector',
  'underscore',
  'mockup-patterns-select2',
  'castle-url/components/content-browser',
  'castle-url/libs/moxie/bin/js/moxie'
], function($, R, cutils, utils, ImageEditor, FocalPointSelector, _,
            Select2, ContentBrowserComponent) {
  'use strict';
  var D = R.DOM;

  var FileListing = R.createClass({
    getInitialState: function(){
      return {
        // image props
        previewUrl: null,
        imageWidth: 0,
        imageHeight: 0,
        previewWidth: 0,
        previewHeight: 0,
        imageFocal: [0, 0],

        title: '',
        description: '',
        youtube_url: '',
        tags: '',
        state: 'review', // possible: (review, uploading, finished, error, crop)
        progress: 0,
        url: '',
        workflow_state: null,
        blob: null,  // customized file
        duplicate: false,
        readonlyFields: [],
        youtubeEnabled: $('body').attr('data-youtube-enabled') === 'true'
      };
    },
    componentDidMount: function(){
      if(!this.state.previewUrl && this.isImage()){
        this.loadImage();
      }
      this.setupTagsWidget();
    },

    componentDidUpdate: function(){
      this.setupTagsWidget();
    },

    setupTagsWidget: function(){
      var that = this;

      if(!that.refs.select2){
        return;
      }

      var options = {
        vocabularyUrl:
          $('body').attr('data-portal-url') +
          "/@@getVocabulary?name=plone.app.vocabularies.Keywords&field=subjects",
        orderable: true,
        allowNewItems: true,
        separator: ";",
        width: '100%'
      };
      var $el = $(that.refs.select2.getDOMNode());
      var select2 = new Select2($el, options);
      $el.off('change').on('change', function(e){
        that.setState({
          tags: e.target.value
        });
      });
    },

    loadImage: function(){
      var that = this;
      var file = that.state.blob || that.props.file;
      var width, height;
      var img = new mOxie.Image();
      img.onload = function() {
        width = img.width;
        height = img.height;
        img.downsize({width: 300});
      };
      img.load(file);
      img.onresize = function(){
        that.setState({
          previewUrl: img.getAsDataURL('image/png'),
          imageWidth: width,
          imageHeight: height,
          imageFocal: [width / 2, height / 2],
          previewWidth: img.width,
          previewHeight: img.height
        });
      };
    },

    valueChanged: function(attr, widget, e){
      if(widget == 'checkbox'){
        this.state[attr] = e.target.checked;
        if (attr === 'upload_to_youtube') {
          if (e.target.checked) {
            this.state.youtube_url = '';
            if (this.state.readonlyFields.indexOf('youtube_url') === -1) {
              this.state.readonlyFields.push('youtube_url')
            }
          } else {
            var idx = this.state.readonlyFields.indexOf('youtube_url');
            if (idx !== -1) {
              this.state.readonlyFields.splice(idx);
            }
          }
        }
      }else{
        this.state[attr] = e.target.value;
      }
      this.forceUpdate();
    },

    render: function(){
      var that = this;
      var file = this.props.file;
      var className = 'file-container';
      var fileName = D.h5({}, file.name + ' (' + this.bytesToSize() + ')');
      var preview = D.span({ className: 'glyphicon glyphicon-file' });
      var content;
      var previewCol = 'col-md-2';
      var fieldsCol = 'col-md-10';

      if(this.state.previewUrl){
        var selector = R.createElement(FocalPointSelector, {
          enabled: this.state.state === 'review',
          url: this.state.previewUrl,
          key: this.props.file.uid + '-image',
          width: this.state.previewWidth,
          fullWidth: this.state.imageWidth,
          height: this.state.previewHeight,
          fullHeight: this.state.imageHeight,
          focalPoint: this.state.imageFocal,
          onFocalSet: function(focal){
            that.setState({
              imageFocal: focal
            });
          }
        });
        preview = selector;
        previewCol = 'col-md-6';
        fieldsCol = 'col-md-6';
      }
      var additional = [];
      if(this.state.state === 'uploading'){
        additional.push(this.renderProgress());
      }else if(this.state.state === 'review'){
        additional.push(this.renderButtons());
        className += ' active';
        if (!this.props.parent.state.update) {
          content = D.div({}, [
            this.renderForm()
          ]);
        }else{
          content = D.div({}, []);
        }
      }else if(this.state.state === 'finished'){
        additional.push(this.renderFinished());
      }else if(this.state.state === 'error'){
        additional.push(D.p({ className: 'error-msg'}, 'There was an error uploading'));
      }else if(this.state.state === 'editimage'){
        content = R.createElement(ImageEditor, {
          file: this.props.file,
          onSave: function(blob){
            that.setState({
              state: 'review',
              blob: blob
            });
            that.loadImage();
          },
          onCancel: function(){
            that.setState({
              state: 'review'
            });
          }});
      }

      return D.li({ id: file.uid, className: className,
                    key: file.uid + '-li' }, [
         D.div({ className: 'row'}, [
          D.div({ className: 'col-xs-12' }, fileName)
        ]),
        D.div({ className: 'row'}, [
          D.div({ className: 'preview-container ' + previewCol }, preview),
          D.div({ className: fieldsCol }, content)
        ]),
        D.div({ className: 'bottom-container'}, additional)
      ]);
    },

    publishClicked: function(e){
      e.preventDefault();
      var that = this;
      utils.loading.show();
      $.ajax({
        url: this.state.base_url + '/@@publish-content',
        data: {
          _authenticator: utils.getAuthenticator()
        }
      }).done(function(){
        that.setState({
          workflow_state: 'published'
        });
      }).fail(function(){
        alert('There was an error publishing content');
      }).always(function(){
        utils.loading.hide();
      });
    },

    renderFinished: function(){
      // should render info on the content, link to it, etc
      var stateAction = [];
      if(this.state.workflow_state !== 'published'){
        stateAction = [
          'This file is currently not published. ',
          D.a({ className: 'content-publish',
                href: '#', onClick: this.publishClicked }, 'Publish immediately')
        ];
      }
      var label = 'Finished uploading ';
      if(this.state.duplicate){
        label = D.span({}, [
          D.b({}, 'Duplicate detected'),
          D.span({}, ': Using file already uploaded: ')
        ]);
      }
      return D.div({className: 'finished-container'}, [
        D.p({}, [
          label,
          D.a({ className: 'content-link',
                href: this.state.base_url + '/view',
                target: '_blank'}, this.state.title),
          '. '
        ].concat(stateAction)),
      ]);
    },

    renderProgress: function(){
      var that = this;
      return D.div({ className: 'castle-progress-container'}, [
        D.div({ className: 'castle-progress'},
          D.span({ className: 'castle-progress-inner', style: { width: that.state.progress + '%'}})),
        D.p({}, 'Uploading ' + that.state.progress + '%')
      ]);
    },

    createField: function(field){
      var name = field['name'];
      var readonly = undefined;
      if (this.state.readonlyFields.indexOf(name) !== -1) {
        readonly = true;
      }

      var input;
      if(field['widget'] == 'checkbox'){
        input = D.input({
          id: id, type: 'checkbox', checked: this.state[name], readOnly: readonly,
          onChange: this.valueChanged.bind(this, name, 'checkbox') })
      }else{
        var nodeType = D.input;
        if(field['widget'] === 'textarea'){
          nodeType = D.textarea;
        }
        input = nodeType({
          className: 'form-control', value: this.state[name], id: id, readOnly: readonly,
          onChange: this.valueChanged.bind(this, name, 'text')});
      }

      var labelClass = 'col-sm-4 control-label';
      if(field['required']){
        labelClass += ' required';
      }

      var id = 'castle-upload-field-' + name;
      return D.div({ className: 'form-group upload-field-' + name }, [
        D.label({ className: labelClass, for_: id}, field['label']),
        D.div({className: 'col-sm-8' }, input)
      ]);
    },

    createTagsField: function(field){
      var labelClass = 'col-sm-4 control-label';
      if(field['required']){
        labelClass += ' required';
      }
      return D.div({ className: "field" }, [
        D.label({className: labelClass}, field['label'] || 'Tags'),
        D.div({ className: 'col-sm-8' },
          D.input({ className: "pat-select2", type: "text", ref: 'select2', value: this.state.tags}))
      ]);
    },

    renderForm: function(){
      var fields = [];
      var self = this;
      this.props.uploadFields.forEach(function(field){
        if(field['for-file-types'] && field['for-file-types'] !== '*'){
          var fileTypes = field['for-file-types'].split(',');
          if(fileTypes.indexOf(self.getType()) === -1){
            return
          }
        }
        if (field['name'] === 'upload_to_youtube' && !self.state.youtubeEnabled) {
          return;
        }

        if(field.widget === 'tags'){
          fields.push(self.createTagsField(field));
        }else{
          fields.push(self.createField(field));
        }
      });
      return D.form({ className: 'form-horizontal', key: this.props.file.uid + '-form' }, fields);
    },

    editImageClicked: function(e){
      e.preventDefault();
      this.setState({
        'state': 'editimage'
      });
    },

    renderButtons: function(){
      var that = this;
      var buttons = [];

      var canApprove = true;
      if (!that.props.parent.state.update) {
        _.each(this.props.requiredFields, function(fieldName){
          if(!that.state[fieldName]){
            canApprove = false;
          }
        });
      }

      if(this.isImage()){
        buttons.push(
          D.button({ className: 'btn btn-default castle-btn-edit', onClick: that.editImageClicked }, 'Edit Image'));
      }
      buttons.push(
        D.button({ className: 'plone-btn plone-btn-default castle-btn-remove', onClick: that.removeClicked },
          D.span({ className: 'icon-remove' }))
      );
      buttons.push(
        D.button({ className: 'plone-btn plone-btn-default castle-btn-upload',
                   onClick: that.approveClicked, disabled: !canApprove },
          D.span({ className: 'icon-ok' }))
      );

      return D.div({ className: 'row' }, D.div({ className: 'col-md-4 col-md-offset-8'}, buttons));
    },

    uploadChunk: function(chunk, id){
      var that = this;
      var chunkSize = 1024 * 1024 * 2;  // 2mb
      var start = (chunk - 1) * chunkSize;
      var end = start + chunkSize;
      var file = that.state.blob || that.props.file;
      var blob = file.slice(start, end);
      if(blob.size === 0){
        utils.loading.hide();
        return;
      }
      utils.loading.show();
      var xhr = new mOxie.XMLHttpRequest();
      var fd = new mOxie.FormData();
      xhr.open('post', $('body').attr('data-portal-url') + '/@@content-creator');
      xhr.responseType = 'json';

      fd.append('chunk', chunk);
      fd.append('action', 'chunk-upload');
      fd.append('file', blob);
      fd.append('name', that.props.file.name);

      if(that.props.parent.props.location){
        fd.append('location', that.props.parent.props.location);
      }
      if(that.state.imageFocal){
        fd.append('focalX', that.state.imageFocal[0]);
        fd.append('focalY', that.state.imageFocal[1]);
      }

      that.props.uploadFields.forEach(function(field){
        if(that.state[field['name']]){
          fd.append(field['name'], that.state[field['name']]);
        }
      });

      fd.append('totalSize', file.size);
      fd.append('chunkSize', chunkSize);
      fd.append('_authenticator', utils.getAuthenticator());

      if(id !== undefined){
        fd.append('id', id);
      }

      if (that.props.parent.state.update) {
        fd.append('content',that.props.parent.state.content);
        fd.append('field', that.props.parent.state.field);
      }

      var sent = Math.round(((start - 1) / file.size) * 100);
      that.setState({
        state: 'uploading',
        progress: sent
      });

      xhr.onload = function() {
        if (xhr.response) {
          if(xhr.response.success){
            if(end < file.size){
              that.uploadChunk(chunk + 1, xhr.response.id);
            }else{
              utils.loading.hide();
              var data = $.extend({}, true, {
                state: 'finished',
                progress: 100
              }, xhr.response);
              that.setState(data);
              that.props.parent.removeUpload(that.props.file.uid);
            }
            return;
          }
        }
        that.setState({
          state: 'error'
        });
        that.props.parent.removeUpload(that.props.file.uid);
        utils.loading.hide();
      };
      xhr.bind('error runtimeerror', function() {
        utils.loading.hide();
        that.setState({
          state: 'error'
        });
        that.props.parent.removeUpload(that.props.file.uid);
        utils.loading.hide();
      });

      xhr.send(fd, {
        runtime_order: 'html5,flash,html4',
        required_caps: {
          send_multipart: true
        }
      });
    },

    approveClicked: function(e){
      e.preventDefault();
      var that = this;
      that.setState({
        state: 'uploading',
        progress: 0
      });
      that.props.parent.addUpload(that.props.file.uid);
    },

    removeClicked: function(e){
      e.preventDefault();
      this.props.parent.removeFile(this.props.idx);
    },

    isImage: function(){
      return this.props.file.type.substring(0, 5) == 'image';
    },

    getType: function(){
      var type = this.props.file.type;
      return type.substring(0, type.indexOf('/'));
    },

    bytesToSize: function() {
      var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      var file = this.state.blob || this.props.file;
      if (file.size === 0) return '0 Byte';
      var i = parseInt(Math.floor(Math.log(file.size) / Math.log(1024)));
      return Math.round(file.size / Math.pow(1024, i), 2) + ' ' + sizes[i];
    },

    getDefaultProps: function(){
      return {
        _id: null,
        parent: null,
        file: null,
        idx: null
      };
    }

  });


  var UploadComponent = {
    getInitialState: function(){
      return {
        files: [],
        dragging: false,
        uploadQueue: [],
        zIndex: 3000,
        shown: false,
        preventClose: false,
        autoUpload: false
      };
    },

    addUpload: function(uid){
      this.state.uploadQueue.push(uid);
      if(this.state.uploadQueue.length === 1){
        this.refs[uid].uploadChunk(1);
      }
      this.state.preventClose = true;
    },

    removeUpload: function(uid){
      // means we can start next one if there is one
      var queue = this.state.uploadQueue;
      var index = queue.indexOf(uid);
      var item = queue[index];
      this.props.onUploadFinished(item, this);
      queue.splice(index, 1);
      this.state.uploadQueue = queue;
      if(queue.length > 0){
        var ref = this.refs[queue[0]];
        if(ref){
          ref.uploadChunk(1);
        }else{
          this.removeUpload(queue[0]);
        }
      }else{
        this.state.preventClose = false;
      }
    },

    afterFilesAdded: function(files){
      var that = this;
      if(that.state.autoUpload){
        files.forEach(function(file){
          that.addUpload(file.uid);
        });
      }
    },

    componentDidMount: function(){
      var that = this;
      if (that.props.update) {
        that.setState({
          update: that.props.update,
          content: that.props.content,
          field: that.props.field,
          autoUpload: that.props.autoUpload
        });
      }else{
        that.setState({
          update: false
        });
      }

      var portalUrl = $('body').attr('data-portal-url');
      mOxie.Env.swf_url = portalUrl + '/++plone++castle/libs/moxie/bin/flash/Moxie.min.swf';
      mOxie.Env.xap_url = portalUrl + '/++plone++castle/libs/moxie/bin/silverlight/Moxie.min.xap';

      var fileInput = new mOxie.FileInput({
        browse_button: that.refs.upload_btn.getDOMNode(),
        runtime_order: 'html5,flash,html4',
        multiple: true,
        // accept: accept
      });

      fileInput.onchange = function(e) {
        that.setState({
          files: that.state.files.concat(e.target.files)
        }, function(){
          that.afterFilesAdded(e.target.files);
        });
      };

      fileInput.init(); // initialize

      var dropEl = this.refs.droparea.getDOMNode();
      var fileDrop = new mOxie.FileDrop({
        drop_zone: dropEl,
        // accept: accept
      });

      fileDrop.ondrop = function() {
        var files = this.files;
        that.setState({
          files: that.state.files.concat(files)
        }, function(){
          that.afterFilesAdded(files);
        });
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
    },

    renderAutoApprove: function(){
      var that = this;
      if(this.getRequiredFields().length > 0){
        return '';
      }
      return D.label({ className: 'checkbox pull-right'}, [
        D.input({ type: 'checkbox', checked: this.state.autoUpload,
                  onClick: function(e){
                    that.setState({
                      autoUpload: e.target.checked
                    });
                  }}),
        'Auto upload'
      ]);
    },

    renderContent: function(){
      var that = this;
      var className = 'castle-upload-container';
      if(that.state.dragging){
        className += ' dragging';
      }
      var dropTxt = '';
      if(that.hasDnd()){
        className += ' dnd-enabled';
        dropTxt = D.div({ className: 'droptext-container'}, [
          D.p({ className: 'upload-text'}, 'Drop files here'),
          D.p({ className: 'upload-text'}, 'or')
        ]);
      }
      if(that.state.files.length > 0){
        className += ' has-files';
      }
      var children = [
        D.div({ ref: 'droparea', className: 'droparea' }, [
          dropTxt,
          D.button({
            ref: 'upload_btn',
            className: 'btn btn-default castle-btn-select-files' }, 'Select files'),
          D.p({className: 'upload-text drop-msg'},
              'Files will be uploaded to central repositories unless you choose folder'),
        ]),
        that.renderAutoApprove(),
        that.renderFileList()
      ]
      var tabs = [
        this.props.parent.renderTabItem('upload')
      ]
      if (!that.state.update) {
        children.splice(1, 0, that.renderUploadLocation());
        tabs.splice(0, 0, this.props.parent.renderTabItem('add'));
      }
      var content = D.div({ className: className }, children);

      return D.div({ className: 'pat-autotoc autotabs fullsize'}, [
        D.nav({ className: 'autotoc-nav'}, tabs),
        content
      ]);
    },

    browsing: true,
    selectFolderClicked: function(){
      var that = this;

      var query = new utils.QueryHelper({
        vocabularyUrl: $('body').attr('data-portal-url') + '/@@getVocabulary?name=plone.app.vocabularies.Catalog',
        batchSize: 18,
        pattern: this,
        sort_on: 'getObjPositionInParent',
        sort_order: 'ascending',
        attributes: ['UID', 'Title', 'portal_type', 'path', 'review_state', 'is_folderish'],
        baseCriteria: [{
          i: 'portal_type',
          o: 'plone.app.querystring.operation.list.contains',
          v: ['Folder']
        }]
      });
      query.currentPath = that.props.location;

      var ContentBrowserBinder = cutils.BindComponentFactoryRoot(
          ContentBrowserComponent, function(){
            return {
              onSelectItem: function(item){
                that.props.location = item.path;
                that.forceUpdate();
              },
              query: query
            };
          }, 'content-browser-react-container');
      ContentBrowserBinder({});
    },

    renderUploadLocation: function(){
      var that = this;
      if(that.props.location){
        return D.div({ className: 'pick-location'}, [
          D.div({ className: 'pick-location-folder'}, D.a({
            className: 'contenttype-folder', href: '#',
            onClick: function(e){
              e.preventDefault();
              that.selectFolderClicked();
            }
          }, ' ')),
          D.div({ className: 'pick-location-location'}, [
            'Upload to: ',
            that.props.location
          ]),
          D.div({ className: 'pick-location-remove'}, D.button({
            className: 'remove',
            onClick: function(e){
              e.preventDefault();
              that.props.location = null;
              that.forceUpdate();
            }
          }, 'x'))
        ]);
      }else{
        return D.div({ className: 'no-location'}, [
          D.a({ className: 'btn btn-default castle-btn-select-files drop-link', href: '#', onClick: function(e){
            e.preventDefault();
            var portalUrl = $('body').attr('data-portal-url');
            var folderUrl = $('body').attr('data-folder-url');
            that.props.location = folderUrl.replace(portalUrl, '') || '/';
            that.forceUpdate();
            that.selectFolderClicked();
          }}, 'Choose Folder')
        ]);
      }
    },

    renderHeader: function(){
      return [
        D.button({ type: 'button', className: 'close', 'data-dismiss': 'modal'}, [
          D.div({ className: 'close-button' }),
          D.span({ 'aria-hidden': 'true' }, '\u00d7')
        ]),
        D.h4({}, 'Upload')
      ];
    },

    renderFooter: function(){
      var buttons = [
        D.button({ type: 'button', className: 'plone-btn plone-btn-primary',
                   'data-dismiss': 'modal'}, 'Done')
      ];
      return D.div({ className: 'btn-container'}, buttons);
    },

    render: function(){
      return D.div({ className: 'modal-content' }, [
        D.div({ className: 'modal-header' }, this.renderHeader()),
        D.div({ className: 'modal-body'}, this.renderContent()),
        D.div({ className: 'modal-footer'}, this.renderFooter())
      ]);
    },

    removeFile: function(idx){
      this.state.files.splice(idx, 1);
      this.setState({
        files: this.state.files
      });
    },

    renderFileList: function(){
      var that = this;
      if(that.state.files.length === 0){
        return '';
      }
      return D.div({ className: 'file-list' }, [
        D.h3({}, 'Files'),
        D.ul({}, that.state.files.map(function(file, idx){
          return R.createElement(FileListing, {
            file: file, ref: file.uid, key: file.uid,
            idx: idx, parent: that, uploadFields: that.getUploadFields()});
        }))
      ]);
    },

    hasDnd: function(){
      return 'draggable' in document.createElement('span') && typeof(window.FileReader) != 'undefined';
    },

    getUploadFields: function(){
      var uploadFields = $('body').attr('data-file-upload-fields');
      if(uploadFields){
        uploadFields = $.parseJSON(uploadFields);
      }else{
        uploadFields = [];
      }
      return uploadFields;
    },

    getRequiredFields: function(){
      var required = [];
      this.getUploadFields().forEach(function(field){
        if(field['required']){
          required.push(field['name'])
        }
      });
      return required;
    },

    getDefaultProps: function(){
      return {
        id: 'upload-content-modal',
        title: 'Upload',
        location: null,
        onUploadFinished: function(){}
      };
    },

    getModalEl: function(){
      return this.props.parent.getModalEl();
    }
  };

  return {
    component: R.createClass(UploadComponent),
    klass: UploadComponent
  };
});
