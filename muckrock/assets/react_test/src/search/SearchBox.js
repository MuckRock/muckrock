import React from 'react';
import SearchActions from '../actions/SearchActions';

var SearchBox = React.createClass({ 

    getInitialState: function() {
        return {
            query: ''
        }
    },

    inputChange: function(event) {
        this.setState({query: event.target.value});
    },

    search: function(e) {
        e.preventDefault();
        SearchActions.search(this.state.query);
    },

    render: function() {
        return (
            <div>
                <label>Search:</label>
                <input type="text" value={this.state.query} onChange={this.inputChange} />
                <button onClick={this.search}>Search</button>
            </div>
        )
    }
});

export default SearchBox;