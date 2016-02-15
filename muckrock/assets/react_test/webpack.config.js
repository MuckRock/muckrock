var webpack = require('webpack');
var path = require('path');
var node_modules_dir = path.resolve(__dirname, 'node_modules');

module.exports = {
    
    devtool: 'eval-source-map',
    
    entry: {
        app: path.resolve(__dirname, './src/App.js')
    },
    
    output: {
         path: __dirname, filename: 'dist/build.js'
    },

    module: {
        loaders: [
            { 
                test: /\.js$/, 
                loader: "babel-loader",
                query: {
                    presets: ['es2015', 'react']
                }
            }
        ]
    }
}