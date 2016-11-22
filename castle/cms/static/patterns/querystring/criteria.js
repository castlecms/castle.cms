define([
  'jquery',
  'castle-url/libs/react/react.min',
  'castle-url/patterns/querystring/widgets/string',
  'castle-url/patterns/querystring/widgets/multipleselection',
  'castle-url/patterns/querystring/widgets/relativedate',
  'castle-url/patterns/querystring/widgets/daterange',
  'castle-url/patterns/querystring/widgets/date',
  'castle-url/patterns/querystring/widgets/reference',
  'castle-url/patterns/querystring/widgets/relativepath',
  'castle-url/patterns/querystring/widgets/select2'
], function($, R, StringWidget, MultipleSelectionWidget, RelativeDateWidget, DateRangeWidget,
            DateWidget, ReferenceWidget, RelativePathWidget, Select2Component){
  'use strict';

  var D = R.DOM;

  return R.createClass({

    widgets: {
      StringWidget: StringWidget,
      MultipleSelectionWidget: MultipleSelectionWidget,
      RelativeDateWidget: RelativeDateWidget,
      DateRangeWidget: DateRangeWidget,
      DateWidget: DateWidget,
      ReferenceWidget: ReferenceWidget,
      RelativePathWidget: RelativePathWidget
    },

    getDefaultProps: function(){
      return {
        indexWidth: '20em',
        classWrapperName: 'querystring-criteria-wrapper',
        classIndexName: 'querystring-criteria-index',
        classOperatorName: 'querystring-criteria-operator',
        classValueName: 'querystring-criteria-value',
        classRemoveName: 'querystring-criteria-remove',
        classResultsName: 'querystring-criteria-results',
        classClearName: 'querystring-criteria-clear',
        i: null,
        o: null,
        v: '',
        idx: -1
      };
    },

    indexSelected: function(e){
      var indexes = this.props.parent.props.indexes;
      var index = indexes[e.target.value];

      this.props.storage.dispatcher.handleViewAction({
        actionType: 'updateCriteria',
        idx: this.props.idx,
        data: {
          i: e.target.value,
          o: index.operations[0],
          v: ''
        }
      });
    },

    operatorSelected: function(e){
      this.props.storage.dispatcher.handleViewAction({
        actionType: 'updateCriteria',
        idx: this.props.idx,
        data: {
          o: e.target.value,
          v: ''
        }
      });
    },

    valueChanged: function(e, force){
      this.props.storage.dispatcher.handleViewAction({
        actionType: 'updateCriteria',
        idx: this.props.idx,
        data: {
          v: e.target.value
        },
        force: force
      });
    },

    removeClicked: function(){
      this.props.storage.dispatcher.handleViewAction({
        actionType: 'removeCriteria',
        idx: this.props.idx,
      });
    },

    render: function(){
      return D.div({ className: this.props.classWrapperName }, [
        D.div({ className: this.props.classRemoveName,
                onClick: this.removeClicked }),
        this.renderIndexSelector(),
        this.renderOperatorSelector(),
        this.renderValueSelector(),
        D.div({ className: 'querystring-criteria-clear'})
      ]);
    },

    renderValueSelector: function(){
      var that = this;
      var indexes = that.props.parent.props.indexes;

      if(!that.props.i || !that.props.o){
        return '';
      }

      var index = indexes[that.props.i];
      var operator = index.operators[that.props.o];
      if(operator.widget === null){
        return '';
      }

      var widget = R.createElement(this.widgets[operator.widget], {
        index: index,
        operator: operator,
        value: this.props.v,
        onChange: this.valueChanged
      });
      return D.div({ className: this.props.classValueName,
                     key: this.props.idx + operator.widget}, widget);
    },

    renderOperatorSelector: function(){
      var that = this;
      var indexes = that.props.parent.props.indexes;

      if(!that.props.i){
        return '';
      }
      var index = indexes[that.props.i];

      var options = [];
      index.operations.forEach(function(operation){
        var operator = index.operators[operation];
        options.push({ value: operation, label: operator.title });
      });

      return D.div({ className: this.props.classOperatorName },
        R.createElement(Select2Component, {
          onChange: this.operatorSelected, options: options, parent: this,
          value: this.props.o })
      );
    },

    renderIndexSelector: function(){
      var options = [{ value: '', label: 'Select criteria'}];
      for (var indexName in this.props.parent.props.indexes) {
        var index = this.props.parent.props.indexes[indexName];
        if(index.enabled){
          options.push({ value: indexName, label: index.title, group: index.group });
        }
      }
      return D.div({ className: this.props.classIndexName },
        R.createElement(Select2Component, {
          onChange: this.indexSelected, options: options, parent: this,
          value: this.props.i, width: this.props.indexWidth, })
      );
    }
  });

});
