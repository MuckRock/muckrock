var path = require('path')
var webpack = require('webpack')
var validate = require('webpack-validator')
var BundleTracker = require('webpack-bundle-tracker')
var ExtractText = require('extract-text-webpack-plugin')

// paths are absolute to the root of the project, where we run `npm` commands
var root = './muckrock/'

var config = {
    devtool: 'source-map',
    entry: {
        main: path.resolve(root + 'assets/entry'),
        foiamachine: path.resolve(root + 'foiamachine/assets/entry'),
    },
    output: {
        path: path.resolve(root + 'assets/bundles/'),
        filename: '[name].js',
    },
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
            {
                test: /\.scss?$/,
                loader: ExtractText.extract('style-loader', 'css-loader?sourceMap!sass-loader?sourceMap'),
            },
            {
                test: /jquery\.js$/,
                loader: 'expose?jQuery!expose?$'
            },
            {
                test: /\.json$/,
                loader: 'json-loader',
            },
        ],
    },
    plugins: [
        new BundleTracker({filename: './muckrock/assets/webpack-stats.json'}),
        new ExtractText('[name].css'),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            "window.jQuery": "jquery"
        }),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
        })
    ],
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
    watchOptions: {
	    poll: true,
    },
};

module.exports = validate(config);
