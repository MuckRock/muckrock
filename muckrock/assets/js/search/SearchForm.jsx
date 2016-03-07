import React from 'react';
import SearchActions from './SearchActions';

var SearchForm = React.createClass({

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
            <form className="search form" onSubmit={this.search}>
                <label>Search</label>
                <input type="text" value={this.state.query} onChange={this.inputChange} />
                <button className="primary" type="submit">Search</button>
            </form>
        )
    }
});

export default SearchForm;
