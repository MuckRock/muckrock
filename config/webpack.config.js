const path = require('path')
const webpack = require('webpack')
const BundleTracker = require('webpack-bundle-tracker')
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
        filename: '[name].js',
        globalObject: 'this'
    },
    plugins: [
        new BundleTracker({filename: './muckrock/assets/webpack-stats.json'}),
        new MiniCssExtractPlugin(),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            jquery: "jquery",
            "window.jQuery": "jquery"
        }),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
        }),
        new webpack.LoaderOptionsPlugin({
            options: {
              context: process.cwd() // or the same value as `context`
            }
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
                test: /\.s[ac]ss?$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    {
                        loader: "css-loader",
                        options: {
                        sourceMap: true
                        }
                    },
                    {
                        loader: "sass-loader",
                        options: {
                        sourceMap: true
                        }
                    }
                ]
            },
            {
                test: require.resolve("jquery"),
                loader: "expose-loader",
                options: {
                  exposes: ["$", "jQuery"],
                },
            },
            {
                test: /\.gif$/,
                loader: 'url-loader'
            }
        ]
    },
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
    watchOptions: {
        poll: true
    }
};

module.exports = config;
