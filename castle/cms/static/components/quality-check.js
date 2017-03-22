/* global define */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'mockup-utils'
], function($, Base, _, R, utils) {
  'use strict';
  var D = R.DOM;

  var countWords = function(string){
    var words = [];
    _.each(string.split(' '), function(word){
      if(word.length > 3){
        words.push(word);
      }
    });
    return words.length;
  };

  var CHECKS = [{
    name: 'Short name format',
    warning: 'starts with "copy", contains a space or contains a capital letter',
    run: function(data, callback){
      if(/copy_?/.test(data.id)){
        return callback(false);
      }
      if(data.id.indexOf(' ') !== -1){
        return callback(false);
      }
      if(data.id.toLowerCase() !== data.id){
        return callback(false);
      }
      return callback(true);
    }
  }, {
    name: 'Title length',
    warning: 'should have no more than 8 significant words',
    run: function(data, callback){
      return callback(countWords(data.title) <= 8);
    }
  }, {
    name: 'Title format',
    warning: 'should begin with upper case letter',
    run: function(data, callback){
      if(data.title[0].toUpperCase() != data.title[0]){
        return callback(false);
      }
      return callback(true);
    }
  }, {
    name: 'Summary length',
    warning: 'should not be empty or have no more than 25 significant words',
    run: function(data, callback){
      if(!data.description){
        return callback(false);
      }
      return callback(countWords(data.description) <= 25);
    }
  }, {
    name: 'Summary format',
    warning: 'should begin with upper case letter',
    run: function(data, callback){
      if(!data.description || data.description[0].toUpperCase() != data.description[0]){
        return callback(false);
      }
      return callback(true);
    }
  }, {
    name: 'Links',
    warning: 'You have links in the content that are referencing unpublished content',
    run: function(data, callback){
      return callback(data.linksValid);
    }
  }, {
    name: 'Headers',
    warning: 'You have headers that are out of order. ' +
             'Headers should be in order of h1, h2, h3, etc and not skip a level.',
    run: function(data, callback){
      return callback(data.headersOrdered);
    }
  }];

  var ATDCheck = {
    name: 'Spelling/Grammar',
    warning: function(component){
      if(component.state.data.atdError){
        return D.span({}, ': Error connecting to AtD to check spelling/grammar.');
      }
      var lis = [];
      component.state.data.atdResponse.forEach(function(error){
        lis.push(D.li({}, [
          D.span({ className: 'desc'}, error.description),
          ': ',
          D.span({ className: 'quote pre'}, '"'),
          D.span({ className: 'string'}, error.string),
          D.span({ className: 'quote post'}, '"'),
        ]));
      });
      return D.ul({className: 'atd-errors'}, lis);
    },
    run: function(data, callback){
      data.atdError = false;
      data.atdResponse = [];
      $.ajax({
        method: 'POST',
        url: $('body').attr('data-base-url') + '/checkDocument',
        data: {
          data: data.html,
          key: 'castle-qualitycheck'
        }
      }).done(function(result){
        var errors = [];
        $(result).find('error').each(function(idx, el){
          var $el = $(el);
          errors.push({
            string: $el.find('string')[0].innerHTML,
            description: $el.find('description')[0].innerHTML,
            precontext: $el.find('precontext')[0].innerHTML,
            type: $el.find('type')[0].innerHTML
          });
        });
        data.atdResponse = errors;
        callback(errors > 0);
      }).fail(function(){
        console.log('Error checking after the deadline');
        data.atdError = true;
        callback(false);
      });
    }
  };

  var QualityCheckComponent = R.createClass({
    getInitialState: function(){
      return {
        checked: {},
        data: {}
      };
    },
    getDefaultProps: function(){
      var checks = CHECKS.slice();
      var tinySettings = $('body').attr('data-pat-tinymce');
      if(tinySettings){
        tinySettings = JSON.parse(tinySettings);
        if(tinySettings.tiny.atd_rpc_url){
          // atd activated for this site...
          checks.push(ATDCheck);
        }
      }

      return {
        delay: true,
        onFinished: function(){},
        checks: checks
      };
    },
    componentDidMount: function(){
      var that = this;
      utils.loading.show();
      var url = $('body').attr('data-base-url');
      if(url === $('body').attr('data-portal-url')){
        url += '/' + $('body').attr('data-site-default');
      }
      $.ajax({
        url: url + '/@@quality-check',
        dataType: 'json',
        cache: false
      }).done(function(data){
        that.check(data);
      }).fail(function(){
        alert('Error checking content');
      }).always(function(){
        utils.loading.hide();
      });
    },
    check: function(data){
      var that = this;
      that.state.data = data;

      var doCheck = function(){
        for(var i=0; i<that.props.checks.length; i++){
          var check = that.props.checks[i];
          if(that.state.checked[check.name] === undefined){
            check.run(data, function(result){
              that.state.checked[check.name] = result;
              that.forceUpdate();
              if(_.size(that.state.checked) !== that.props.checks.length){
                if(that.props.delay){
                  setTimeout(doCheck, [250, 500, 750, 1000][Math.floor(Math.random()*4)]);
                }else{
                  doCheck();
                }
              }else{
                that.props.onFinished();
              }
            });
            break;
          }
        }
      };
      doCheck();
    },
    done: function(){
      return _.size(this.state.checked) === this.props.checks.length;
    },
    isValid: function(){
      var that = this;
      for(var i=0; i<that.props.checks.length; i++){
        var check = that.props.checks[i];
        if(!this.state.checked[check.name]){
          return false;
        }
      }
      return true;
    },
    render: function(){
      var that = this;
      var info = '';
      if(that.done()){
        if(that.isValid()){
          info = D.div({ className: 'portalMessage info'}, [
            D.strong({}, 'Success'),
            'All checks are successful.'
          ]);
        }else{
          info = D.div({ className: 'portalMessage error'}, [
            D.strong({}, 'Double check'),
            'Problems have been detected. It is recommended you fix them.'
          ]);
        }
      }
      return D.div({ className: 'castle-quality'}, [D.ul({}, that.props.checks.map(function(check){
        var className = '';
        var label = check.name;
        var labelExtra = '';
        var value = that.state.checked[check.name];
        if(value !== undefined){
          if(value){
            className = 'glyphicon glyphicon-ok';
          }else{
            className = 'glyphicon glyphicon-remove';
            if(typeof(check.warning) != 'function'){
              label += ': ' + check.warning;
            }else{
              labelExtra = check.warning(that);
            }
          }
        }
        return D.li({}, [
          D.span({ className: className}),
          label,
          labelExtra
        ]);
      })),
        info
      ]);
    },
  });

  return QualityCheckComponent;
});
