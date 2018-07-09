/* global define */

define([
  'jquery',
  'pat-base',
  'mockup-utils'
], function($, Base, utils) {
  'use strict';

  var FormPattern = Base.extend({
    name: 'castledynamicform',
    trigger: '.pat-castledynamicform',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      var self = this;
      var $form = self.$el.parents('form');
      if($form.size() === 0){
        return;
      }
      self.$form = $form;
      self.bind();
      self.manipulate();
    },
    manipulate: function(){
      // show/hide stuff
      var self = this;
      var $useQuery = self.getUseQuery();
      if($useQuery.size() === 1){
        if($('input', self.getUseQuery())[0].checked){
          self.getQuery().show();
          self.getLimit().show();
          self.getContent().hide();
        }else{
          self.getQuery().hide();
          self.getLimit().hide();
          self.getContent().show();
        }
      }
      var $useDesc = self.getUseDescription();
      if($useDesc.size() === 1){
        if($('input', self.getUseDescription())[0].checked){
          self.getCustomText().hide();
        }else{
          self.getCustomText().show();
        }
      }
      var $navType = self.getNavType();
      if($navType.size() === 1){
        var val = $navType.val();
        if(val === 'query'){
          self.getQuery().show();
          self.getContent().hide();
        }else if(val === 'content'){
          self.getQuery().hide();
          self.getContent().show();
        }else{
          self.getQuery().hide();
          self.getContent().hide();
        }
      }
    },
    bind: function(){
      var self = this;
      $('input', self.getUseQuery()).change(function(){
        self.manipulate();
      });
      $('input', self.getUseDescription()).change(function(){
        self.manipulate();
      });
      self.getNavType().change(function(){
        self.manipulate();
      });
    },
    getLimit: function(){
      return $('div[id$="-limit"]', this.$form);
    },
    getUseQuery: function(){
      return $('div[id$="-use_query"]', this.$form);
    },
    getUseDescription: function(){
      return $('div[id$="-use_description"]', this.$form);
    },
    getQuery: function(){
      return $('div[id$="-query"]', this.$form);
    },
    getContent: function(){
      return $('div[id$="-content"],div[id$="-images"]', this.$form);
    },
    getCustomText: function(){
      return $('div[id$="-custom_text"]', this.$form);
    },
    getNavType: function(){
      return $('#castle-cms-navigation-nav_type', this.$form);
    }
  });
  return FormPattern;

});
