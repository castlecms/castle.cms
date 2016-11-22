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

  var _checks = [{
    name: 'Short name format',
    warning: 'starts with "copy", contains a space or contains a capital letter',
    run: function(data){
      if(/copy_?/.test(data.id)){
        return false;
      }
      if(data.id.indexOf(' ') !== -1){
        return false;
      }
      if(data.id.toLowerCase() !== data.id){
        return false;
      }
      return true;
    }
  }, {
    name: 'Title length',
    warning: 'should have no more than 8 significant words',
    run: function(data){
      return countWords(data.title) <= 8;
    }
  }, {
    name: 'Title format',
    warning: 'should begin with upper case letter',
    run: function(data){
      if(data.title[0].toUpperCase() != data.title[0]){
        return false;
      }
      return true;
    }
  }, {
    name: 'Summary length',
    warning: 'should not be empty or have no more than 25 significant words',
    run: function(data){
      if(!data.description){
        return false;
      }
      return countWords(data.description) <= 25;
    }
  }, {
    name: 'Summary format',
    warning: 'should begin with upper case letter',
    run: function(data){
      if(!data.description || data.description[0].toUpperCase() != data.description[0]){
        return false;
      }
      return true;
    }
  }, {
    name: 'Links',
    warning: 'You have links in the content that are referencing unpublished content',
    run: function(data){
      return data.linksValid;
    }
  }, {
    name: 'Headers',
    warning: 'You have headers that are out of order. ' +
             'Headers should be in order of h1, h2, h3, etc and not skip a level.',
    run: function(data){
      return data.headersOrdered;
    }
  }];

  var QualityCheckComponent = R.createClass({
    getInitialState: function(){
      return {
        checked: {}
      };
    },
    getDefaultProps: function(){
      return {
        delay: true,
        onFinished: function(){}
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
      var doCheck = function(){
        for(var i=0; i<_checks.length; i++){
          var check = _checks[i];
          if(that.state.checked[check.name] === undefined){
            that.state.checked[check.name] = check.run(data);
            that.forceUpdate();
            break;
          }
        }
        if(_.size(that.state.checked) !== _checks.length){
          if(that.props.delay){
            setTimeout(doCheck, [250, 500, 750, 1000][Math.floor(Math.random()*4)]);
          }else{
            doCheck();
          }
        }else{
          that.props.onFinished();
        }
      };
      doCheck();
    },
    done: function(){
      return _.size(this.state.checked) === _checks.length;
    },
    isValid: function(){
      for(var i=0; i<_checks.length; i++){
        var check = _checks[i];
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
      return D.div({ className: 'castle-quality'}, [D.ul({}, _checks.map(function(check){
        var className = '';
        var label = check.name;
        var value = that.state.checked[check.name];
        if(value !== undefined){
          if(value){
            className = 'glyphicon glyphicon-ok';
          }else{
            className = 'glyphicon glyphicon-remove';
            label += ': ' + check.warning;
          }
        }
        return D.li({}, [
          D.span({ className: className}),
          label
        ]);
      })),
        info
      ]);
    },
  });

  return QualityCheckComponent;
});
