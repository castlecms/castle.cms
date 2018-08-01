define([
  'jquery',
  'castle-url/libs/react/react.min',
  'castle-url/patterns/querystring/criteria',
  'castle-url/patterns/querystring/widgets/select2',
  'castle-url/components/utils'
], function($, R, CriteriaComponent, Select2Component, cutils){
  'use strict';

  var D = R.DOM;

  return R.createClass({
    getInitialState: function(){
      return {
        sortOn: '',
        reversed: false,
        criterias: []
      };
    },

    getDefaultProps: function(){
      return {
        afterChange: function(){}
      };
    },

    componentDidMount: function() {
      this.props.storage.store.addChangeListener('change', this._onChange);
    },

    componentWillUnmount: function() {
      this.props.storage.store.removeChangeListener('change', this._onChange);
    },

    _onChange: function(){
      var that = this;
      this.setState(this.props.storage.store.getData(), function(){
        that.props.afterChange();
      });
    },

    reverseClicked: function(e){
      this.props.storage.dispatcher.handleViewAction({
        actionType: 'update',
        data: {
          reversed: e.target.checked
        }
      });
    },

    sortOnChanged: function(e){
      this.props.storage.dispatcher.handleViewAction({
        actionType: 'update',
        data: {
          sortOn: e.target.value
        }
      });
    },

    addCriteriaClicked: function(e){
      e.preventDefault();
      this.props.storage.dispatcher.handleViewAction({
        actionType: 'addCriteria',
        data: {
          i: '',
          o: '',
          v: ''
        }
      });
    },

    render: function(){
      return D.div({ className: this.props.classWrapperName }, [
        this.renderCriterias(),
        D.div({ className: this.props.classAddCriteriaName,
                style: { clear: 'both'}}, [
          D.button({ className: 'plone-btn plone-btn-default plone-btn-xs',
                     onClick: this.addCriteriaClicked }, 'Add criteria')
        ]),
        this.renderSorting()
      ]);
    },

    renderCriterias: function(){
      var that = this;

      if(this.state.criterias.length === 0){
        return D.p({ className: 'querystring-empty-criterias'}, 'No criteria defined.');
      }

      var criterias = [];

      this.state.criterias.forEach(function(criteria, idx){
        criterias.push(R.createElement(CriteriaComponent, cutils.extend(criteria, {
          parent: that,
          idx: idx,
          storage: that.props.storage
        })));
      });

      return criterias;
    },

    getQueryString: function(){
      var results = [];
      this.state.criterias.forEach(function(criteria){
        if(!criteria.i || !criteria.o){
          return;
        }
        results.push(criteria);
      });
      return results;
    },

    renderSorting: function(){
      var options = [{ value: '', label: 'No sorting'}];
      for (var key in this.props.sortable_indexes) {
        var index = this.props.sortable_indexes[key];
        options.push({ value: key, label: index.title});
      }

      return D.div({ className: this.props.classSortWrapperName }, [
        D.span({ className: this.props.classSortLabelName }, 'Sort on'),
        R.createElement(Select2Component, {
          parent: this, onChange: this.sortOnChanged,
          options: options, value: this.state.sortOn,
          ref: 'sortOn' }),
        D.label({ className: this.props.classSortReverseName }, [
          D.input({ type: 'checkbox', onClick: this.reverseClicked,
                    checked: this.state.reversed,
                    ref: 'sortOrder' }),
          'Reversed Order'
        ]),
        // D.div({}, JSON.stringify(this.getQueryString())),
        // D.div({}, 'Sort on: ' + this.state.sortOn),
        // D.div({}, 'Reversed: ' + this.state.reversed),
      ]);
    }
  });

  //
  // [{"i": "portal_type", "o": "plone.app.querystring.operation.selection.any", "v": ["Event"]},
  //  {"i": "review_state", "o": "plone.app.querystring.operation.selection.any", "v": ["published"]}]
});
