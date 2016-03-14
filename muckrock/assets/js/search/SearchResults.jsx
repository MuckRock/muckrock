import React from 'react';
import alt from './alt';
import SearchStore from './SearchStore';

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
        console.log(state);
        this.setState({results: state.results, searchMade: true});
    },

    render: function() {
        console.log(this.state);
        var results = this.state.results.map((result) => {
            return (
                <li className="search results item">
                    {result}
                </li>
            )
        });
        if (results.length < 1 && this.state.searchMade) {
            results = 'no results';
        }
        return (
            <ul className="search results list">
                {results}
            </ul>
        )
    }
});

export default SearchResults;
