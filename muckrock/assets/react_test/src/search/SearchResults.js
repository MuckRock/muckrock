import React from 'react';
import alt from '../alt';
import SearchStore from '../stores/SearchStore';
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
        console.log('onchange', state);
        this.setState({results: state.results});
    },
    render: function() {
        console.log('results state', this.state);
        var results = this.state.results.map((result) => {
            return (
                <li>{result}</li>
            )
        });
        return (
            <div>
                <ul>
                    {results}
                </ul>
            </div>
        )
    }
});
export default SearchResults;