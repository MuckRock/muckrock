import React from 'react';
import alt from './alt';
import SearchStore from './SearchStore';

var SearchResults = React.createClass({

    getInitialState: function() {
        return {
            results: []
        }
    },

    componentDidMount: function() {
        SearchStore.listen(this.onChange);
    },

    componentWillUnmount: function() {
        SearchStore.unlisten(this.onChange);
    },

    onChange(state) {
        console.debug('Results state:', this.state);
    },

    render: function() {
        var results = this.state.results.map((result) => {
            return (
                <li className="search results item">
                    {result}
                </li>
            )
        });
        return (
            <ul className="search results list">
                {results}
            </ul>
        )
    }
});

export default SearchResults;
