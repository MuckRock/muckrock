import React from 'react';
import alt from './alt';
import SearchStore from './SearchStore';

var SearchResult = React.createClass({
    render: function() {
        var result = this.props.result;
        return (
            <div className="search-result">
                <p><a href="{result.url}">{result.title}</a></p>
            </div>
        )
    }
});

var SearchResults = React.createClass({

    getInitialState: function() {
        return {
            results: [],
            searchMade: false
        }
    },

    componentDidMount: function() {
        SearchStore.listen(this.onChange);
    },

    componentWillUnmount: function() {
        SearchStore.unlisten(this.onChange);
    },

    onChange(state) {
        console.log('Results changed.');
        console.debug(state);
        this.setState({results: state.results, searchMade: true});
    },

    render: function() {
        console.debug(this.state);
        var results = this.state.results.map((result, index) => {
            return (
                <li key={index} className="search-results-item">
                    <SearchResult result={result} />
                </li>
            )
        });
        var resultsCounter = '0 results';
        if (results.length == 1) {
            resultsCounter = '1 result';
        } else if (results.length > 1) {
            resultsCounter = results.length + ' results';
        }
        return (
            <div className="search-results">
                <p>{resultsCounter}</p>
                <ul className="search-results-list">
                    {results}
                </ul>
            </div>
        )
    }
});

export default SearchResults;
