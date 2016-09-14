/* webpack.config.production.js
**
** Provides a production configuration for Webpack
** by importing and modifying the base configuration.
*/

var webpack = require('webpack');
var merge = require('webpack-merge');
var validate = require('webpack-validator');

var config = require('./webpack.config.js');

productionConfig = merge(config, {
  plugins: [
    new webpack.optimize.UglifyJsPlugin({
        compress: {
            warnings: false
        }
    }),
  ]
});

module.exports = validate(productionConfig);
