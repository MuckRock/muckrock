import React from 'react';
import SearchBox from './SearchBox';
import SearchResults from './SearchResults';

var SearchContainer = React.createClass({ 
    render: function() {
    	var divStyle = {
    		display: 'inline-block',
			padding: '5px'
    	};
        return (
            <div style={divStyle}>
                <SearchBox />
                <SearchResults />
            </div>
        )
    }
});
export default SearchContainer;