/* global define, google */

define([
  'jquery',
  'mockup-patterns-base',
  'underscore',
  'castle-url/libs/react/react.min',
  'mockup-utils',
  'castle-url/components/modal',
  'castle-url/components/utils',
  'moment',
  'castle-url/libs/script'
], function($, Base, _, R, utils, Modal, cutils, moment, $script) {
  'use strict';
  var D = R.DOM;

  var Chart = R.createClass({
    getDefaultProps: function(){
      return {
        height: '500px'
      };
    },
    componentDidMount: function(){
      var chart = new this.props.Type(this.refs.chart.getDOMNode());
      chart.draw(this.props.data, this.props.options);
    },
    componentDidUpdate: function(){
      this.componentDidMount();
    },
    render: function(){
      return D.div({ ref: 'chart', key: this.props.key || this.props.name,
                     style: { height: this.props.height} });
    }
  });


  var BaseTab = {
    type: 'realtime',

    labels: {
      'referralPath': 'Referral',
      'deviceCategory': 'Device type',
      'pagePath': 'Page'
    },

    dimensionOptions: [],
    metricOptions: [],

    translate: function(name){
      if(this.labels[name]){
        return this.labels[name];
      }else{
        name = name.replace('rt:', '').replace('ga:', '');
        if(this.labels[name]){
          return this.labels[name];
        }
      }
      name = name.replace('avg', 'average').replace('pageviews', 'pageViews');
      var label = name.substring(0, 1).toUpperCase();
      name.substring(1).split('').forEach(function(letter){
        if(letter === letter.toUpperCase()){
          label += ' ' + letter.toLowerCase();
        }else{
          label += letter;
        }
      });
      return label;
    },

    getInitialState: function(){
      return {
        loading: true,
        chartsLoaded: false,
        metrics: this.metricOptions[0],
        dimensions: null,
        sort: null,
        max_results: 5,
        global: false,
        data: {},
        paths: [],
        chartType: 'column'
      };
    },

    componentDidMount: function(){
      var that = this;
      this.load();

      // because callbacks are fun
      if(window.google && window.google.charts){
        that.setState({
          chartsLoaded: true
        });
        return;
      }
      $script('https://www.gstatic.com/charts/loader.js', function(){
        google.charts.load('current', {'packages':['corechart', 'bar']});
        google.charts.setOnLoadCallback(function(){
          that.setState({
            chartsLoaded: true
          });
        });
      });
    },

    getQueryData: function(){
      var query = {
        metrics: this.state.metrics,
        'global': this.state.global,
        sort: '-' + this.state.metrics
      };
      if(this.state.dimensions){
        query.dimensions = this.state.dimensions;
      }
      if(this.state.max_results){
        query.max_results = this.state.max_results;
      }
      return query;
    },

    load: function(){
      var that = this;
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-base-url') + '/@@content-analytics',
        data: {
          api: 'ga',
          type: this.type,
          params: JSON.stringify(that.getQueryData()),
          cache_duration: 60 * 5
        }
      }).done(function(data){
        data.loading = false;
        that.setState({
          loading: false,
          data: data.data,
          paths: data.paths
        });
      }).fail(function(){
        alert('failed to load analytic data');
      }).always(function(){
        utils.loading.hide();
      });
    },

    timedLoad: function(){
      var that = this;
      if(this._timeout){
        clearTimeout(this._timeout);
      }
      this._timeout = setTimeout(function(){
        that.load();
      }, 500);
    },

    changeValue: function(param, e){
      var value = e.target.value;
      this.state[param] = value;
      this.forceUpdate();
      this.timedLoad();
    },

    globalClicked: function(e){
      this.setState({
        global: e.target.checked
      });
      this.timedLoad();
    },

    createOption: function(val, name){
      if(!name){
        name = this.translate(val);
      }
      return D.option({ value: val}, name);
    },

    render: function(){
      var that = this;

      if(that.state.loading || !that.state.chartsLoaded){
        return D.p({}, 'Loading data...');
      }
      if(!this.state.data){
        return D.p({}, 'No data could be retrieved. Google Analytics API support may not be configured.');
      }
      var cdata = [['Count', this.translate(this.state.metrics)]];
      _.each(this.state.data.rows, function(result){
        if(result.length > 1) {
          cdata.push([result[0] + '', parseInt(result[1])]);
        } else {
          cdata.push([result[0], parseInt(result[0])]);
        }
      });
      cdata = google.visualization.arrayToDataTable(cdata);

      // Set chart options
      var options = {
        title: 'Real time statistics',
        hAxis: {
          title: 'Count',
          minValue: 0
        },
        vAxis: {
          title: this.translate(this.state.metrics)
        }
      };

      var chartType = google.visualization.ColumnChart;
      if(this.state.chartType === 'pie'){
        chartType = google.visualization.PieChart;
      }
      var chart = 'No data found';
      if(this.state.data.rows){
        chart = R.createElement(Chart, {
          name: 'context',
          data: cdata,
          options: options,
          Type: chartType
        });
      }

      return D.div({},
        this.renderFields(),
        chart,
        D.div({ className: 'checkbox pull-right'}, D.label({}, [
          D.input({ type: 'checkbox', checked: this.state.global,
                    onClick: this.globalClicked }),
          'Analyze entire site'
        ])),
        D.p({ className: 'discreet'}, 'Totals for current page: ' + $('body').attr('data-base-url'))
      );
    },
    renderFields: function(){
      var that = this;

      var dimensions = [that.createOption('', 'N/A')];
      this.dimensionOptions.forEach(function(dim){
        dimensions.push(that.createOption(dim));
      });
      var metrics = [];
      this.metricOptions.forEach(function(metric){
        metrics.push(that.createOption(metric));
      });

      var fields = [
        D.div({ className: "form-group col-md-2" }, [
          D.label({ }, 'Aggregate'),
          D.select({ className: 'form-control',
                     value: this.state.metrics,
                     onChange: this.changeValue.bind(this, 'metrics')}, metrics)
        ]),
        D.div({ className: "form-group col-md-2" }, [
          D.label({ }, 'Dimensions'),
          D.select({ className: 'form-control',
                     value: this.state.dimensions,
                     onChange: this.changeValue.bind(this, 'dimensions')}, dimensions)
        ]),
        D.div({ className: "form-group col-md-2" }, [
          D.label({ }, 'Max results'),
          D.select({ className: 'form-control',
                     value: this.state.max_results,
                     onChange: this.changeValue.bind(this, 'max_results')}, [
            D.option({ value: '5'}, '5'),
            D.option({ value: '10'}, '10'),
            D.option({ value: '15'}, '15')
          ])
        ]),
        D.div({ className: "form-group col-md-2" }, [
          D.label({ }, 'Chart type'),
          D.select({ className: 'form-control',
                     value: this.state.chartType,
                     onChange: this.changeValue.bind(this, 'chartType')}, [
            D.option({ value: 'column'}, 'Columns'),
            D.option({ value: 'pie'}, 'Pie')
          ])
        ])
      ].concat(this.renderAdditionalFields());
      return D.div({ className: "row" }, fields);
    },
    renderAdditionalFields: function(){
      // to add custom fields, override
      return [];
    }
  };


  var RealtimeTab = cutils.Class([BaseTab], {
    type: 'realtime',
    dimensionOptions: [
      'rt:userType',
      'rt:medium',
      'rt:trafficType',
      'rt:browser',
      'rt:operatingSystem',
      'rt:deviceCategory',
      'rt:country',
      'rt:region',
      'rt:pagePath'
    ],
    metricOptions: [
      'rt:pageViews',
      'rt:activeUsers'
    ]
  });

  var HistoryTab = cutils.Class([BaseTab], {
    type: 'ga',
    dimensionOptions: [
      'ga:userType',
      'ga:sessionCount',
      'ga:socialNetwork',
      'ga:hasSocialSourceReferral',
      'ga:medium',
      'ga:trafficType',
      'ga:browser',
      'ga:operatingSystem',
      'ga:deviceCategory',
      'ga:pagePath',
      'ga:country',
      'ga:region',
      'ga:continent',
      'ga:subContinent',
      'ga:metro',
      'ga:city',
      'ga:flashVersion',
      'ga:javaEnabled',
      'ga:language',
      'ga:exitPagePath'
    ],
    metricOptions: [
      'ga:hits',
      'ga:users',
      'ga:newUsers',
      'ga:sessions',
      'ga:pageviews',
      'ga:bounces',
      'ga:bounceRate',
      'ga:avgSessionDuration',
      'ga:entranceRate',
      'ga:pageviewsPerSession',
      'ga:avgTimeOnPage',
      'ga:avgPageLoadTime'
    ],

    getInitialState: function(){
      var state = BaseTab.getInitialState.call(this);
      state.to = moment().local().format('YYYY-MM-DD');
      state.from = moment().local().subtract(7, 'days').format('YYYY-MM-DD');
      return state;
    },

    componentDidUpdate: function(){
      var that = this;
      if(this.refs.from){
        $(this.refs.from.getDOMNode()).pickadate({
          format: 'yyyy-mm-dd',
          formatSubmit: 'yyyy-mm-dd',
          onSet: function(context){
            that.state.from = moment(context.select).local().format('YYYY-MM-DD');
            that.timedLoad();
          }
        });
        $(this.refs.to.getDOMNode()).pickadate({
          format: 'yyyy-mm-dd',
          formatSubmit: 'yyyy-mm-dd',
          onSet: function(context){
            that.state.to = moment(context.select).local().format('YYYY-MM-DD');
            that.timedLoad();
          }
        });
      }
    },

    getQueryData: function(){
      var data = BaseTab.getQueryData.call(this);
      var now = moment().local();
      var dfrom = moment(this.state.from, "YYYY-MM-DD").local();
      var dto = moment(this.state.to, "YYYY-MM-DD").local();
      data.start_date = parseInt((now - dfrom) / 1000 / 60 / 60 / 24) + 'daysAgo';
      data.end_date = parseInt((now - dto) / 1000 / 60 / 60 / 24) + 'daysAgo';
      return data;
    },

    renderAdditionalFields: function(){
      return [
        D.div({ className: "form-group col-md-2" }, [
          D.label({ }, 'From'),
          D.input({ className: 'form-control', ref: 'from',
                    value: this.state.from })
        ]),
        D.div({ className: "form-group col-md-2" }, [
          D.label({ }, 'To'),
          D.input({ className: 'form-control', ref: 'to',
                    value: this.state.to })
        ])
      ];
    }
  });


  var AnalyticsModalComponent = cutils.Class([Modal], {
    dataMappings: {
      pinterest: 'Pinterest',
      twitter_matomo: 'Twitter (Matomo)',
      facebook_matomo: 'Facebook (Matomo)'
    },
    getInitialState: function(){
      return {
        social: null,
        analytics: null,
        tab: 'realtime',
        loading: false
      };
    },
    componentDidMount: function(){
      Modal.componentDidMount.call(this);
      var that = this;
      utils.loading.show();
      $.ajax({
        url: $('body').attr('data-base-url') + '/@@content-analytics',
        data: {
          api: 'social'
        }
      }).done(function(data){
        that.setState({
          social: data.data
        });
      }).fail(function(){
        alert('failed to load analytic data');
      }).always(function(){
        utils.loading.hide();
      });
    },
    tabClicked: function(tab){
      this.setState({
        tab: tab
      });
    },
    renderTabItem: function(tab, label){
      return D.a({ href: '#' + tab, className: this.state.tab === tab && 'active' || '',
                   onClick: this.tabClicked.bind(this, tab)}, label);
    },
    renderContent: function(){
      var that = this;
      if(that.state.loading){
        return D.div({ className: 'castle-analytics'}, [
          D.p({ className: 'discreet'}, 'Loading analytic data...')
        ]);
      }
      return D.div({ className: 'castle-analytics pat-autotoc autotabs'}, [
        D.nav({ className: 'autotoc-nav'}, [
          that.renderTabItem('realtime', 'Real time'),
          that.renderTabItem('history', 'Historical'),
          that.renderTabItem('social', 'Social')
        ]),
        that.renderTab()
      ]);
    },
    renderTab: function(){
      if(this.state.tab === 'realtime'){
        return R.createElement(RealtimeTab, {
          parent: this
        });
      }
      if(this.state.tab === 'history'){
        return R.createElement(HistoryTab, {
          parent: this
        });
      }
      if(this.state.tab === 'social'){
        return this.renderSocialTab();
      }
    },
    renderSiteTab: function(){
      if(this.state.analytics === null){
        return D.p({ className: 'discreet' }, 'Analytics API not configured');
      }

      var data = this.state.analytics;
      var cdata = google.visualization.arrayToDataTable([
        ['Type', 'Count', { role: 'style' }, { role: 'annotation' }],
        ['Users', data.activeUsers, 'color: gray', data.activeUsers],
        ['Page Views', data.activePageViews, 'color: #76A7FA', data.activePageViews]
      ]);

      // Set chart options
      var options = {
        title: 'Real-time data'
      };
      return R.createElement(Chart, {
        name: 'site',
        data: cdata,
        options: options,
        Type: google.visualization.ColumnChart
      });
    },
    renderSocialTab: function(){
      var that = this;
      if(this.state.social === null){
        return D.p(
          { className: 'discreet' },
          'No social data found (Make sure social count monitoring is configured)');
      }
      var extra = '';
      var data = this.state.social;
      var cdata= [
        ['Platform', 'Shares']
      ];
      Object.keys(this.dataMappings).forEach(function(dataKey){
        if(data[dataKey]){
          cdata.push([that.dataMappings[dataKey], data[dataKey]]);
        }
      });

      if(data.twitter){
        cdata.push(['Twitter', data.twitter]);
        extra = D.p(
          { className: 'discreet'},
          'Twitter shares as reported via Twitter\'s streaming API');
      }else if(!data.twitter_matomo){
        extra = D.p(
          { className: 'discreet'},
          'Twitter API keys may not be set (Make sure twitter monitoring is configured)');
      }

      cdata = google.visualization.arrayToDataTable(cdata);

      // Set chart options
      var options = {
        title: 'Social media shares',
        hAxis: {
          title: 'Platform',
          minValue: 0
        },
        vAxis: {
          title: 'Shares'
        }
      };
      return [
        R.createElement(Chart, {
          name: 'realtime',
          key: 'realtime-' + this.state.metrics + this.state.dimensions +
               this.state.max_results + this.state.chartType,
          data: cdata,
          options: options,
          Type: google.visualization.ColumnChart
        }),
        extra];
    },
    renderFooter: function(){
      var buttons = [D.button({ type: 'button', className: 'plone-btn plone-btn-primary',
                                'data-dismiss': 'modal'}, 'Done')];
      return D.div({}, buttons);
    },
    getDefaultProps: function(){
      return $.extend({}, true, Modal.getDefaultProps.apply(this), {
        id: 'analytics-content-modal',
        title: 'Content Analytics',
        width: '95%'
      });
    }
  });

  return AnalyticsModalComponent;
});