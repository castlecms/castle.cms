define([
  'jquery',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/utils'
], function($, R, utils, cutils){
  'use strict';

  var D = R.DOM;

  return R.createClass({

    getDefaultProps: function(){
      return {
        value: ''
      };
    },

    getDepth: function(){
      var value = this.props.value;
      if(!value){
        return -1;
      }
      if(value.indexOf('::') === -1){
        return -1;
      }
      return value.split('::')[1];
    },

    getPath: function(){
      var value = this.props.value;
      if(!value){
        return '';
      }
      if(value.indexOf('::') === -1){
        return value;
      }
      return value.split('::')[0];
    },

    browseClicked: function(e){
      var that = this;
      e.preventDefault();

      var tinyConfig = JSON.parse($('body').attr('data-pat-tinymce'));
      var query = new utils.QueryHelper({
        vocabularyUrl: tinyConfig.relatedItems.vocabularyUrl,
        batchSize: 30,
        sort_on: 'getObjPositionInParent',
        sort_order: 'ascending',
        attributes: ['UID', 'Title', 'portal_type', 'path', 'review_state', 'is_folderish']
      });
      // get current path instead?
      query.pattern.browsing = true;
      query.currentPath = '/';

      var ContentBrowserComponent = require('castle-url/components/content-browser');
      var ContentBrowserBinder = cutils.BindComponentFactoryRoot(
        ContentBrowserComponent, function(){
          return {
            onSelectItem: function(item){
              that.props.onChange({
                target: {
                  value: item.path + '::' + that.getDepth()
                }
              });
              that.props.value = item.path + '::' + that.getDepth();
            },
            query: query,
            multiple: false
          };
        }, 'content-browser-react-container');

      ContentBrowserBinder({});
      $('#content-browser-react-container').off('click').on('click', function(){
        // reopen query widget if opened...
        var $query = $('#popover-structure-query.active');
        if($query.length > 0){
          setTimeout(function(){
            $query.parent().find('.input-group-btn a').trigger('click');
          }, 10);
        }
      });
    },

    depthChange: function(e){
      var that = this;
      var depth = e.target.value;
      that.props.onChange({
        target: {
          value: that.getPath() + '::' + depth
        }
      });
      that.props.value = that.getPath() + '::' + depth;

    },

    render: function(){
      var that = this;

      var selected = '';
      if(that.getPath()){
        selected = D.span({}, [
          D.b({}, 'Selected: '),
          that.getPath()
        ]);
      }

      var depthOptions = [D.option({ value: '-1'}, 'Unlimited')];
      [0, 1, 2, 3, 4, 5].forEach(function(number){
        depthOptions.push(D.option({ value: number}, number));
      });

      return D.div({ className: 'querystring-reference-widget'}, [
        selected,
        D.button({ className: 'plone-btn plone-btn-default plone-btn-xs',
                   onClick: this.browseClicked }, 'Browse'),
        D.div({ className: "depth-select-box form-group" }, [
          D.label({ htmlFor: "depth-select" }, 'Depth'),
          D.select({ name: "depth-select", onChange: this.depthChange,
                     value: this.getDepth(),
                     className: "querystring-criteria-depth form-control" }, depthOptions)
        ])
      ]);
    }
  });

});
