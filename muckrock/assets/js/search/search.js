import React from 'react';
import ReactDOM from 'react-dom';
import SearchForm from './SearchForm';
import SearchResults from './SearchResults';

var Search = React.createClass({
    render: function() {
        return (
            <div className="search container">
                <SearchForm />
                <SearchResults />
            </div>
        )
    }
});

var container = document.getElementById('react-search');
if (container) {
    ReactDOM.renderComponent(<Search />, container);
}

export default Search;
