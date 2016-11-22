const path = require('path');
const webpack = require('webpack');

function resolve(base) {
  return base.startsWith('/') ? base
    : path.resolve(path.join(path.dirname(__filename), base));
}

function resolver(base) {
  return function (sub) {
    return resolve(base ? (
      sub ? path.join(resolve(base), sub) : resolve(base)
    ) : (
      sub ? resolve(sub) : __dirname
    ));
  };
}

const JQUERY_RECURRENCE = resolver('%(bower)s/jquery.recurrenceinput.js');

const LOGGING = resolver('%(bower)s/logging');
const TINYMCE = resolver('%(bower)s/tinymce-builded');
const PATTERNSLIB = resolver('%(bower)s/patternslib');
const MOCKUP = resolver('%(mockup)s');

const CMFPLONE = resolver('%(cmfplone)s');
const MOSAIC = resolver('%(mosaic)s');
const CASTLE = resolver('%(castle)s');

//const WEBPACK = resolver('./src/theme/webpack');

var alias = %(aliases)s;

// brace is a webpack compat version of the ace editor that we need to override with
alias.ace = "brace";

function AddToContextPlugin(condition, extras) {
  this.condition = condition;
  this.extras = extras || [];
}

// http://stackoverflow.com/questions/30065018/
// dynamically-require-an-aliased-module-using-webpack
AddToContextPlugin.prototype.apply = function (compiler) {
  const condition = this.condition;
  const extras = this.extras;
  var newContext = false;
  compiler.plugin('context-module-factory', function (cmf) {
    cmf.plugin('after-resolve', function (items, callback) {
      newContext = true;
      return callback(null, items);
    });
    // this method is called for every path in the ctx
    // we just add our extras the first call
    cmf.plugin('alternatives', function (items, callback) {
      if (newContext && items[0].context.match(condition)) {
        newContext = false;
        var alternatives = extras.map(function (extra) {
          return {
            context: items[0].context,
            request: extra
          };
        });
        items.push.apply(items, alternatives);
      }
      return callback(null, items);
    });
  });
};

module.exports = {
  resolve: {

    alias: alias

  },
  module: {
    loaders: [

      { test: /\.(png|gif|otf|eot|svg|ttf|woff|woff2)(\?.*)?$/,
        loader: 'url?limit=8192' },

      { test: alias.tinymce,
        loader: 'imports?document=>window.document,this=>window!exports?window.tinymce' },

      { test: /tinymce\/plugins/,
        loader: 'imports?tinymce,this=>{tinymce:tinymce}' },

      { test: alias['jquery.recurrenceinput'],
        loader: 'imports?tmpl=jquery.tmpl' },

      { test: alias['jquery.event.drop'],
        loader: 'exports?$.drop' },

      //{ test: alias['jquerytools.tabs'],
      //  loader: 'exports?$.tabs' },

      { test: /backbone\.paginator/,
        loader: 'imports?_=underscore' },

      { test: /PloneFormGen.*quickedit\.js$/,
        loader: 'imports?requirejs=>define,_tabs=jquerytools.tabs' },

      { test: alias['mockup-patterns-texteditor'],
        loader: [
          'imports?ace=ace',
          '_a=ace/mode/javascript',
          '_b=ace/mode/text',
          '_c=ace/mode/css',
          '_d=ace/mode/html',
          '_e=ace/mode/xml',
          '_f=ace/mode/less',
          '_g=ace/mode/python',
          '_h=ace/mode/xml',
          '_i=ace/mode/ini'
        ].join(',')
      }
    ]
  },
  plugins: [

    // Fix generic issue where now and then we expect jQuery to be
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
      'window.jQuery': 'jquery'
    }),

    // Fix issues where css-loader left url()s with relative paths
    new webpack.NormalModuleReplacementPlugin(
      new RegExp('^\./[^\.]+\.(png|gif)$'), function(ob) {
        switch(ob.request) {
          case './prev.gif':
          case './next.gif':
          case './pb_close.png':
            ob.request = resolve(
              path.join(JQUERY_RECURRENCE('lib'), ob.request));
            break;
          case './jqtree-circle.png':
            ob.request = 'jqtree/jqtree-circle.png';
            break;
        }
      }
    ),

    // Fix plone.app.mosaic icon paths
    new webpack.NormalModuleReplacementPlugin(
      new RegExp('plone.app.mosaic.images'), function(ob) {
        ob.request = path.join(MOSAIC('browser/static/img'),
          path.basename(ob.request));
      }
    ),

    // Fix dynamic requires in structure pattern
    // https://github.com/plone/mockup/commit/89de866dff89a455bd4102c84a3fa8f9a0bcc34b
    new webpack.ContextReplacementPlugin(
      new RegExp('patterns\/structure'),
      new RegExp('^\.\/.*$|^mockup-patterns-structure-url/.*$')
    ),
    new AddToContextPlugin(
      new RegExp('patterns\/structure'), [
        'mockup-patterns-structure-url/js/actions.js',
        'mockup-patterns-structure-url/js/actionmenu.js',
        'mockup-patterns-structure-url/js/navigation.js',
        'mockup-patterns-structure-url/js/collections/result.js'
      ]
    )
  ]
};
