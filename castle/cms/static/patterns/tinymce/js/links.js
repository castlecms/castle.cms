define([
  'jquery',
  'underscore',
  'pat-registry',
  'pat-base',
  'tinymce',
  'text!mockup-patterns-tinymce-url/templates/link.xml',
  'text!mockup-patterns-tinymce-url/templates/image.xml',
  'mockup-patterns-relateditems',
  'castle-url/components/utils',
  'mockup-utils',
  'mockup-patterns-autotoc',
  'mockup-patterns-modal'
], function($, _, registry, Base, tinymce, LinkTemplate, ImageTemplate, RelatedItems, cutils, utils) {
  'use strict';

  var DIRECT_URL_TYPE = '_direct_';

  var LinkType = Base.extend({
    defaults: {
      linkModal: null // required
    },

    init: function() {
      this.linkModal = this.options.linkModal;
      this.tinypattern = this.options.tinypattern;
      this.tiny = this.tinypattern.tiny;
      this.dom = this.tiny.dom;
    },

    getEl: function(){
      return this.$el.find('input').first();
    },

    value: function() {
      return $.trim(this.getEl().val());
    },

    toUrl: function() {
      return this.value();
    },

    load: function(element) {
      this.getEl().attr('value', this.tiny.dom.getAttrib(element, 'data-val'));
    },

    set: function(val) {
      var $el = this.getEl();
      $el.attr('value', val);
      $el.val(val);
    },

    attributes: function() {
      return {
        'data-val': this.value()
      };
    }
  });

  var ExternalLink = LinkType.extend({
    init: function() {
      LinkType.prototype.init.call(this);
      this.getEl().on('change', function(){
        // check here if we should automatically add in http:// to url
        var val = $(this).val();
        if((new RegExp("https?\:\/\/")).test(val)){
          // already valid url
          return;
        }
        var domain = $(this).val().split('/')[0];
        if(domain.indexOf('.') !== -1){
          $(this).val('http://' + val);
        }
      });
    }
  });

  var InternalLink = LinkType.extend({
    init: function() {
      LinkType.prototype.init.call(this);
      this.getEl().addClass('pat-relateditems');
      this.createRelatedItems();
    },

    getEl: function(){
      return this.$el.find('input:not(.select2-input)').first();
    },

    createRelatedItems: function() {
      this.relatedItems = new RelatedItems(this.getEl().first(),
        this.linkModal.options.relatedItems);
    },

    value: function() {
      var val = this.getEl().val();
      if (val){
        if(typeof(val) === 'object') {
          val = val[0];
        } else if(typeof(val) === "string"){
          val = {
            UID: val
          };
        }
      }
      return val;
    },

    toUrl: function() {
      var value = this.value();
      if (value) {
        return this.tinypattern.generateUrl(value);
      }
      return null;
    },
    load: function(element) {
      var val = this.tiny.dom.getAttrib(element, 'data-val');
      if (val) {
        this.set(val);
      }
    },

    set: function(val) {
      var $el = this.getEl().first();
      $el[0].component.setState({
        selected: [val]
      });
      $el[0].component.selectionUpdated();
    },

    attributes: function() {
      var val = this.value();
      if (val) {
        return {
          'data-val': val.UID
        };
      }
      return {};
    }
  });

  var ImageLink = InternalLink.extend({
    toUrl: function() {
      var value = this.value();
      return this.tinypattern.generateImageUrl(value, this.linkModal.$scale.val());
    },
    createRelatedItems: function() {
      // slightly different because we want to start browsing at /image-repository
      this.relatedItems = new RelatedItems(this.getEl().first(),
        cutils.extend(this.linkModal.options.relatedItems, {
          initialPath: '/image-repository'
        }));
    }
  });

  var EmailLink = LinkType.extend({
    toUrl: function() {
      var self = this;
      var val = self.value();
      if (val) {
        var subject = self.getSubject();
        var href = 'mailto:' + val;
        if (subject) {
          href += '?subject=' + subject;
        }
        return href;
      }
      return null;
    },

    load: function(element) {
      LinkType.prototype.load.apply(this, [element]);
      this.linkModal.$subject.val(this.tiny.dom.getAttrib(element, 'data-subject'));
    },

    getSubject: function() {
      return this.linkModal.$subject.val();
    },

    attributes: function() {
      var attribs = LinkType.prototype.attributes.call(this);
      attribs['data-subject'] = this.getSubject();
      return attribs;
    }
  });

  var AnchorLink = LinkType.extend({
    init: function() {
      LinkType.prototype.init.call(this);
      this.$select = this.$el.find('select');
      this.anchorNodes = [];
      this.anchorData = [];
      this.populate();
    },

    value: function() {
      var val = this.$select.val();
      if (val) {
        return this.findData(val);
      }
      return;
    },

    updated: function(){
      this.populate();
    },

    populate: function() {
      var self = this;
      self.anchorNodes = [];
      self.anchorData = [];

      self.addAnchors(
        $('a.mceItemAnchor,img.mceItemAnchor,a.mce-item-anchor,img.mce-item-anchor,a[id]:not([href])'));

      var selected = self.linkModal.linkTypes.internal.value();
      if(selected && selected.UID){
        selected = selected.UID && selected.UID || selected;
        // use ajax to get the contents of the page and find anchor tags
        $.ajax({
          url: $('body').attr('data-portal-url') + '/resolveuid/' + selected + '/view'
        }).done(function(data){
          var $dom = $(utils.parseBodyTag(data));
          var title = _.find($.parseHTML(data), function(el){ return el.tagName === 'TITLE'; });
          if(title){
            title = title.innerHTML;
          }else{
            title = undefined;
          }
          self.addAnchors($('a[id]:not([href])', $dom), title + ': ', selected);
          // initial loading probably failed, try again now...
          var id = self.$select.attr('data-selected');
          self.createSelect2(id);
        }).fail(function(){
          self.createSelect2();
        });
      }else {
        self.createSelect2();
      }
    },

    addAnchors: function(nodes, prefix, uid){
      var self = this;
      var node, i, name, id;
      if(!prefix){
        prefix = '';
      }
      for (i = 0; i < nodes.length; i = i + 1) {
        node = nodes[i];
        id = self.tiny.dom.getAttrib(node, 'id');
        name = self.tiny.dom.getAttrib(node, 'name');
        if (!name) {
          name = id;
        }
        if(!id){
          id = name;
        }
        if (id !== '') {
          self.anchorNodes.push(node);
          self.anchorData.push({name: name, label: prefix + name, id: id, uid: uid});
        }
      }
    },

    createSelect2: function(selected){
      var self = this;
      self.$select.select2("destroy");
      self.$select.empty();
      var i;
      if (self.anchorNodes.length > 0) {
        for (i = 0; i < self.anchorData.length; i = i + 1) {
          var data = self.anchorData[i];
          var id = self.getAnchorId(data);
          var $option = $("<option value='" + id + "'>" + data.label + '</option>');
          if(selected == id){
            $option[0].selected = true;
          }
          self.$select.append($option);
        }
      } else {
        self.$select.append('<option>No anchors found..</option>');
      }
      this.$select.select2();
    },

    getAnchorId: function(data){
      var id = data.id;
      if(data.uid){
        id += data.uid;
      }
      return id;
    },

    findData: function(id){
      var self = this;
      for(var i=0; i<self.anchorData.length; i++){
        if(id === self.getAnchorId(self.anchorData[i])){
          return self.anchorData[i];
        }
      }
    },

    toUrl: function() {
      var val = this.value();
      if (val) {
        if(val.uid){
          return this.linkModal.linkTypes.internal.toUrl() + '#' + val.id;
        }else{
          return '#' + val.id;
        }
      }
      return null;
    },

    attributes: function(){
      var val = this.value();
      return {
        'data-val': val.uid,
        'data-id': this.getAnchorId(val)
      };
    },

    load: function(el){
      var $el = $(el);
      var uid = $el.attr('data-val');
      var id = $el.attr('data-id');
      this.$select.attr('data-selected', id);
      var data = this.findData(id);
      if(data){
        this.set(data);
      }
      // load link type as well
      if(uid){
        this.linkModal.linkTypes.internal.load($el);
      }
    },

    set: function(data) {
      var id = this.getAnchorId(data);
      this.$select.select2('data', id);
    }
  });

  tinymce.PluginManager.add('ploneimage', function(editor) {
    editor.addButton('ploneimage', {
      icon: 'image',
      tooltip: 'Insert/edit image',
      onclick: editor.settings.addImageClicked,
      stateSelector: 'img:not([data-mce-object])'
    });

    editor.addMenuItem('ploneimage', {
      icon: 'image',
      text: 'Insert image',
      onclick: editor.settings.addImageClicked,
      context: 'insert',
      prependToContext: true
    });
  });

  /* register the tinymce plugin */
  tinymce.PluginManager.add('plonelink', function(editor) {
    editor.addButton('plonelink', {
      icon: 'link',
      tooltip: 'Insert/edit link',
      shortcut: 'Ctrl+K',
      onclick: editor.settings.addLinkClicked,
      stateSelector: 'a[href]'
    });

    editor.addButton('unlink', {
      icon: 'unlink',
      tooltip: 'Remove link(s)',
      cmd: 'unlink',
      stateSelector: 'a[href]'
    });

    editor.addShortcut('Ctrl+K', '', editor.settings.addLinkClicked);

    editor.addMenuItem('plonelink', {
      icon: 'link',
      text: 'Insert link',
      shortcut: 'Ctrl+K',
      onclick: editor.settings.addLinkClicked,
      stateSelector: 'a[href]',
      context: 'insert',
      prependToContext: true
    });
  });


  var LinkModal = Base.extend({
    name: 'linkmodal',
    trigger: '.pat-linkmodal',
    defaults: {
      anchorSelector: 'h1,h2,h3',
      linkTypes: [
        /* available, none activate by default because these options
         * only get merged, not set.
        'internal',
        'modallink',
        'external',
        'email',
        'anchor',
        'image'
        'externalImage'*/
      ],
      initialLinkType: 'internal',
      text: {
        insertHeading: 'Insert Link'
      },
      linkTypeClassMapping: {
        'internal': InternalLink,
        'modallink': InternalLink,
        'external': ExternalLink,
        'email': EmailLink,
        'anchor': AnchorLink,
        'image': ImageLink,
        'externalImage': LinkType
      }
    },
    // XXX: this is a temporary work around for having separated templates.
    // Image modal is going to have its own modal class, funcs and template.
    linkTypeTemplateMapping: {
      'internal': LinkTemplate,
      'modallink': LinkTemplate,
      'external': LinkTemplate,
      'email': LinkTemplate,
      'anchor': LinkTemplate,
      'image': ImageTemplate,
      'externalImage': ImageTemplate
    },

    template: function(data) {
      return _.template(this.linkTypeTemplateMapping[this.linkType])(data);
    },

    init: function() {
      var self = this;
      self.$selectedTile = $('.mosaic-selected-tile');

      self.tinypattern = self.options.tinypattern;
      if (self.tinypattern.options.anchorSelector) {
        self.options.anchorSelector = self.tinypattern.options.anchorSelector;
      }
      self.tiny = self.tinypattern.tiny;
      self.dom = self.tiny.dom;
      self.linkType = self.options.initialLinkType;
      self.urlType = '/view';
      self.linkTypes = {};

      self.modal = registry.patterns['plone-modal'].init(self.$el, {
        html: self.generateModalHtml(),
        content: null,
        buttons: '.plone-btn'
      });
      self.modal.on('shown', function(e) {
        self.modalShown.apply(self, [e]);
      });
      self.modal.on('hide', function(e) {
        if(self.$selectedTile.length > 0){
          var Tile = require('mosaic-url/mosaic.tile');
          var tile = new Tile(self.$selectedTile);
          tile.select();
        }
        self.tiny.selection.setRng(self.rng);
      });
    },

    isOnlyTextSelected: function() {
      /* pulled from TinyMCE link plugin */
      var html = this.tiny.selection.getContent();

      // Partial html and not a fully selected anchor element
      if (/</.test(html) && (!/^<a [^>]+>[^<]+<\/a>$/.test(html) || html.indexOf('href=') === -1)) {
        return false;
      }

      if (this.anchorElm) {
        var nodes = this.anchorElm.childNodes, i;

        if (nodes.length === 0) {
          return false;
        }

        for (var ii = nodes.length - 1; ii >= 0; ii--) {
          if (nodes[ii].nodeType !== 3) {
            return false;
          }
        }
      }

      return true;
    },

    generateModalHtml: function() {
      return this.template({
        options: this.options,
        text: this.options.text,
        insertHeading: this.options.text.insertHeading,
        linkTypes: this.options.linkTypes,
        externalText: this.options.text.external,
        emailText: this.options.text.email,
        subjectText: this.options.text.subject,
        targetList: this.options.targetList,
        titleText: this.options.text.title,
        externalImageText: this.options.text.externalImage,
        altText: this.options.text.alt,
        imageAlignText: this.options.text.imageAlign,
        scaleText: this.options.text.scale,
        scales: this.options.scales,
        cancelBtn: this.options.text.cancelBtn,
        insertBtn: this.options.text.insertBtn
      });
    },

    isImageMode: function() {
      return ['image', 'externalImage'].indexOf(this.linkType) !== -1;
    },

    emitLinkLoaded: function(){
      var self = this;
      _.each(self.options.linkTypes, function(type) {
        if(self.linkTypes[type].updated){
          self.linkTypes[type].updated();
        }
      });
    },

    initElements: function() {
      var self = this;
      self.$selectedTile = $('.mosaic-selected-tile');
      self.$target = $('select[name="target"]', self.modal.$modal);
      self.$button = $('.plone-modal-footer input[name="insert"]', self.modal.$modal);
      self.$title = $('input[name="title"]', self.modal.$modal);
      self.$subject = $('input[name="subject"]', self.modal.$modal);
      self.$urlTypeContainer = $('.urltype', self.modal.$modal);
      self.$urlType = $('select[name="urlType"]', self.$urlTypeContainer);
      self.$urlTypeContainer.hide();

      self.$alt = $('input[name="alt"]', self.modal.$modal);
      self.$align = $('select[name="align"]', self.modal.$modal);
      self.$scale = $('select[name="scale"]', self.modal.$modal);

      /* load up all the link types */
      _.each(self.options.linkTypes, function(type) {
        var $container = $('.linkType.' + type + ' .main', self.modal.$modal);
        self.linkTypes[type] = new self.options.linkTypeClassMapping[type]($container, {
          linkModal: self,
          tinypattern: self.tinypattern
        });
        if(type === 'internal' || type === 'modallink'){
          var relatedItems = self.linkTypes[type].relatedItems;
          relatedItems.$el.on('loaded', function(){
            var item = relatedItems.component.state.items[0];
            if(item && ['File', 'Video', 'Audio', 'Image'].indexOf(item.portal_type) !== -1){
              self.$urlTypeContainer.show();
            }else{
              self.$urlTypeContainer.hide();
              self.urlType = DIRECT_URL_TYPE;
              self.$urlType.val(DIRECT_URL_TYPE);
            }
            self.emitLinkLoaded();
          });
        }
      });

      $('.autotoc-nav a', self.modal.$modal).click(function() {
        var $fieldset = $('fieldset.linkType', self.modal.$modal).eq($(this).index());
        var classes = $fieldset[0].className.split(/\s+/);
        _.each(classes, function(val) {
          if (_.indexOf(self.options.linkTypes, val) !== -1){
            self.linkType = val;
          }
        });
      });

      self.data = {};
      // get selection BEFORE..
      // This is pulled from TinyMCE link plugin
      self.initialText = null;
      var value;
      self.rng = self.tiny.selection.getRng();
      self.selectedElm = self.tiny.selection.getNode();
      self.anchorElm = self.tiny.dom.getParent(self.selectedElm, 'a[href]');
      self.onlyText = self.isOnlyTextSelected();

      self.data.text = self.initialText = self.anchorElm ? (self.anchorElm.innerText || self.anchorElm.textContent) : self.tiny.selection.getContent({format: 'text'});
      self.data.href = self.anchorElm ? self.tiny.dom.getAttrib(self.anchorElm, 'href') : '';

      if (self.anchorElm) {
        self.data.target = self.tiny.dom.getAttrib(self.anchorElm, 'target');
      } else if (self.tiny.settings.default_link_target) {
        self.data.target = self.tiny.settings.default_link_target;
      }

      if ((value = self.tiny.dom.getAttrib(self.anchorElm, 'rel'))) {
        self.data.rel = value;
      }

      if ((value = self.tiny.dom.getAttrib(self.anchorElm, 'class'))) {
        self.data['class'] = value;
      }

      if ((value = self.tiny.dom.getAttrib(self.anchorElm, 'title'))) {
        self.data.title = value;
      }

      // always default to first tab...
      $('.autotoc-nav a:first', self.modal.$modal).trigger('click');
    },

    getLinkUrl: function() {
      // get the url, only get one uid
      return this.linkTypes[this.linkType].toUrl();
    },

    getValue: function() {
      return this.linkTypes[this.linkType].value();
    },

    updateAnchor: function(href) {
      var self = this;

      self.urlType = self.$urlType.val() || DIRECT_URL_TYPE;

      self.tiny.focus();
      self.tiny.selection.setRng(self.rng);

      if((self.linkType === 'internal' || self.linkType === 'modallink') &&
         self.urlType !== DIRECT_URL_TYPE){
        href += self.urlType;
      }

      var target = self.$target.val();
      var title = self.$title.val();
      var linkAttrs = $.extend(true, self.data, {
        title: title ? title : null,
        target: target ? target : null,
        'data-linkType': self.linkType,
        'data-urltype': self.urlType,
        href: href
      }, self.linkTypes[self.linkType].attributes());
      if (self.anchorElm) {

        if (self.onlyText && linkAttrs.text !== self.initialText) {
          if ("innerText" in self.anchorElm) {
            self.anchorElm.innerText = self.data.text;
          } else {
            self.anchorElm.textContent = self.data.text;
          }
        }

        self.tiny.dom.setAttribs(self.anchorElm, linkAttrs);

        self.tiny.selection.select(self.anchorElm);
        self.tiny.undoManager.add();
      } else {
        if (self.onlyText) {
          self.tiny.insertContent(
            self.tiny.dom.createHTML('a', linkAttrs,
                                     self.tiny.dom.encode(self.data.text)));
        } else {
          self.tiny.execCommand('mceInsertLink', false, linkAttrs);
        }
      }
    },

    focusElement: function(elm) {
      this.tiny.focus();
      this.tiny.selection.select(elm);
      this.tiny.nodeChanged();
    },

    updateImage: function(src) {
      var self = this;
      var title = self.$title.val();

      self.tiny.focus();
      self.tiny.selection.setRng(self.rng);

      var data = $.extend(true, {}, {
        src: src,
        title: title ? title : null,
        alt: self.$alt.val(),
        'class': 'image-' + self.$align.val(),
        'data-linkType': self.linkType,
        'data-scale': self.$scale.val()
      }, self.linkTypes[self.linkType].attributes());
      if (self.imgElm && !self.imgElm.getAttribute('data-mce-object')) {
        data.width = self.dom.getAttrib(self.imgElm, 'width');
        data.height = self.dom.getAttrib(self.imgElm, 'height');
      } else {
        self.imgElm = null;
      }

      function waitLoad(imgElm) {
        imgElm.onload = imgElm.onerror = function() {
          imgElm.onload = imgElm.onerror = null;
          self.focusElement(imgElm);
        };
      }

      if (!self.imgElm) {
        data.id = '__mcenew';
        self.tiny.insertContent(self.dom.createHTML('img', data));
        self.imgElm = self.dom.get('__mcenew');
        self.dom.setAttrib(self.imgElm, 'id', null);
      } else {
        self.dom.setAttribs(self.imgElm, data);
      }

      waitLoad(self.imgElm);
      if (self.imgElm.complete) {
        self.focusElement(self.imgElm);
      }
    },

    modalShown: function(e) {
      var self = this;
      self.initElements();
      self.initData();

      self.$button.off('click').on('click', function(e) {
        self.hide();
        e.preventDefault();
        e.stopPropagation();
        self.linkType = self.modal.$modal.find('fieldset.active').data('linktype');
        var href;
        try{
            href = self.getLinkUrl();
        }catch(error){
            return;  // just cut out if no url
        }
        if (!href) {
          return; // just cut out if no url
        }
        if (self.isImageMode()) {
          self.updateImage(href);
        } else {
          /* regular anchor */
          self.updateAnchor(href);
        }
      });
      $('.plone-modal-footer input[name="cancel"]', self.modal.$modal).click(function(e) {
        e.preventDefault();
        self.hide();
      });
    },

    show: function() {
      this.modal.show();
    },

    hide: function() {
      this.modal.hide();
    },

    initData: function() {
      var self = this;
      self.selection = self.tiny.selection;
      self.tiny.focus();
      var selectedElm = self.imgElm = self.selection.getNode();
      self.anchorElm = self.dom.getParent(selectedElm, 'a[href]');

      var linkType;
      if (self.isImageMode()) {
        if (self.imgElm.nodeName !== 'IMG') {
          // try finding elsewhere
          if (self.anchorElm) {
            var imgs = self.anchorElm.getElementsByTagName('img');
            if (imgs.length > 0) {
              self.imgElm = imgs[0];
              self.focusElement(self.imgElm);
            }
          }
        }
        if (self.imgElm.nodeName !== 'IMG') {
          // okay, still no image, unset
          self.imgElm = null;
        }
        if (self.imgElm) {
          var src = self.dom.getAttrib(self.imgElm, 'src');
          self.$title.val(self.dom.getAttrib(self.imgElm, 'title'));
          self.$alt.val(self.dom.getAttrib(self.imgElm, 'alt'));
          linkType = self.dom.getAttrib(self.imgElm, 'data-linktype');
          if (linkType) {
            self.linkType = linkType;
            self.linkTypes[self.linkType].load(self.imgElm);
            var scale = self.dom.getAttrib(self.imgElm, 'data-scale');
            if(scale){
              self.$scale.val(scale);
            }
            $('#tinylink-' + self.linkType, self.modal.$modal).trigger('click');
          }else if (src) {
            self.guessImageLink(src);
          }
          var className = self.dom.getAttrib(self.imgElm, 'class');
          var klasses = className.split(' ');
          for (var i = 0; i < klasses.length; i = i + 1) {
            var klass = klasses[i];
            if (klass.indexOf('image-') !== -1) {
              self.$align.val(klass.replace('image-', ''));
            }
          }
        }
      }else if (self.anchorElm) {
        self.focusElement(self.anchorElm);
        var href = '';
        href = self.dom.getAttrib(self.anchorElm, 'href');
        self.$target.val(self.dom.getAttrib(self.anchorElm, 'target'));
        self.$title.val(self.dom.getAttrib(self.anchorElm, 'title'));
        linkType = self.dom.getAttrib(self.anchorElm, 'data-linktype');
        if (linkType) {
          self.linkType = linkType;
          self.linkTypes[self.linkType].load(self.anchorElm);
          $('#tinylink-' + self.linkType, self.modal.$modal).trigger('click');
        }else if (href) {
          self.guessAnchorLink(href);
        }
        var urlType = self.dom.getAttrib(self.anchorElm, 'data-urltype');
        if(urlType){
          self.urlType = urlType;
          self.$urlType.val(urlType);
        }
      }
    },

    guessImageLink: function(src) {
      if (src.indexOf(this.options.prependToScalePart) !== -1) {
        this.linkType = 'image';
        this.$scale.val(this.tinypattern.getScaleFromUrl(src));
        this.linkTypes.image.set(this.tinypattern.stripGeneratedUrl(src));
      } else {
        this.linkType = 'externalImage';
        this.linkTypes.externalImage.set(src);
      }
    },

    guessAnchorLink: function(href) {
      if (this.options.prependToUrl &&
          href.indexOf(this.options.prependToUrl) !== -1) {
        // XXX if using default configuration, it gets more difficult
        // here to detect internal urls so this might need to change...
        this.linkType = 'internal';
        this.linkTypes.internal.set(this.tinypattern.stripGeneratedUrl(href));
      } else if (href.indexOf('mailto:') !== -1) {
        this.linkType = 'email';
        var email = href.substring('mailto:'.length, href.length);
        var split = email.split('?subject=');
        this.linkTypes.email.set(split[0]);
        if (split.length > 1) {
          this.$subject.val(decodeURIComponent(split[1]));
        }
      } else if (href[0] === '#') {
        this.linkType = 'anchor';
        this.linkTypes.anchor.set(href.substring(1));
      } else {
        this.linkType = 'external';
        this.linkTypes.external.set(href);
      }
    },

    setSelectElement: function($el, val) {
      $el.find('option:selected').prop('selected', false);
      if (val) {
        // update
        $el.find('option[value="' + val + '"]').prop('selected', true);
      }
    },

    reinitialize: function() {
      /*
       * This will probably be called before show is run.
       * It will overwrite the base html template given to
       * be able to privde default values for the overlay
       */
      this.modal.options.html = this.generateModalHtml();
    }
  });
  return LinkModal;

});
