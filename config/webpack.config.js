var path = require('path')
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

// paths are absolute to the root of the project, where we run `npm` commands
var root = './muckrock/'

module.exports = {
    context: __dirname,
    entry: path.resolve(root + 'assets/js/index'),
    output: {
        path: path.resolve(root + 'assets/bundles/'),
        filename: '[name].js',
    },
    plugins: [
        new BundleTracker({filename: './muckrock/webpack-stats.json'}),
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
