const webpack = require('webpack');
const join = require('path').join;
const resolve = require('path').resolve;
const merge = require('webpack-merge');
const path = require('path');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const WriteFileWebpackPlugin = require('write-file-webpack-plugin');


const common = merge(require('./webpack/webpack.globals'), {
  // Define bundles
  cache: true,
  debug: false,
  devtool: "eval",
  entry: %(bundles_config)s,
  output: %(output)s,
  module: {
    exprContextCritical: false,  // structure pattern has dynamic requires
    loaders: [
      { test: require.resolve('jquery'), loader: 'expose?$!expose?jQuery' },
      { test: /\.less$/,
        loaders: [
          'style',
          'css',
          'less'
        ]
      },
      { test: /\.scss$/,
        loaders: [
          'style',
          'css',
          'sass'
        ]
      }
    ]
  },
  plugins: [
    new webpack.optimize.OccurenceOrderPlugin(true),
    new webpack.optimize.CommonsChunkPlugin({
      name: "%(common)s",
      chunks: %(bundles_keys)s
    }),
    // new webpack.optimize.UglifyJsPlugin({
    //   compress: { warnings: false },
    //   sourceMap: false
    // })
  ],
  resolve: {
    root: [ path.join(__dirname, 'src') ],
    extensions: ['', '.js']
  }
});

module.exports = common;
