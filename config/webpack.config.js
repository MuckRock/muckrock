var path = require('path')
var webpack = require('webpack')
// var validate = require('webpack-validator')
var BundleTracker = require('webpack-bundle-tracker')
const MiniCssExtractPlugin = require("mini-css-extract-plugin")

// paths are absolute to the root of the project, where we run `npm` commands
var root = './muckrock/'

var config = {
    mode: 'development',
    devtool: 'source-map',
    entry: {
        main: path.resolve(root + 'assets/entry'),
        foiamachine: path.resolve(root + 'foiamachine/assets/entry'),
        docViewer: path.resolve(root + 'assets/js/docViewer')
    },
    output: {
        path: path.resolve(root + 'assets/bundles/'),
        filename: '[name].js'
    },
    plugins: [
        new BundleTracker({filename: './muckrock/assets/webpack-stats.json'}),
        new MiniCssExtractPlugin(),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            "window.jQuery": "jquery"
        }),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
        })
    ],
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env', '@babel/preset-react']
                    }
                }
            },
            {
                test: /\.scss?$/,
                use: [MiniCssExtractPlugin.loader, 'style-loader', 'css-loader?sourceMap', 'sass-loader?sourceMap']
            },
            {
                test: /jquery\.js$/,
                use: ['expose?jQuery', 'expose'],
            },
            {
                test: /\.json$/,
                loader: 'json-loader',
            },
            {
                test: /\.gif$/,
                loader: 'url-loader',
            },
        ],
    },
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
    watchOptions: {
        poll: true
    }
};

module.exports = config;
