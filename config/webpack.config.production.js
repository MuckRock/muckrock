/* webpack.config.production.js
**
** Provides a production configuration for Webpack
** by importing and modifying the base configuration.
*/

var webpack = require('webpack');
var merge = require('webpack-merge');
const TerserPlugin = require("terser-webpack-plugin");
var config = require('./webpack.config.js');

productionConfig = merge(config, {
    mode: 'production',
    optimization: {
        minimize: true,
        // see Terser plugin options:
        // https://github.com/webpack-contrib/terser-webpack-plugin#terseroptions
        minimizer: [new TerserPlugin()],
    },
});

module.exports = productionConfig;
