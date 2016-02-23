var path = require('path')
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

var root = './muckrock/'

module.exports = {
    context: __dirname,
    entry: root + 'assets/js/index',
    output: {
        path: path.resolve(root + 'assets/bundles/'),
        filename: '[name]-[hash].js',
    },
    plugins: [
        new BundleTracker({filename: root + 'webpack-stats.json'}),
    ],
    module: {
        loaders: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                loader: 'babel-loader',
                query: {
                    presets: ['es2015', 'react'],
                }
            },
        ],
    },
    resolve: {
        moduleDirectories: ['node_modules'],
        extensions: ['', '.js', '.jsx']
    },
}
