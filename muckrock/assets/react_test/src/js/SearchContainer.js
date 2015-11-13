var SearchBox = require('./SearchBox');
var React = require('react');

var SearchContainer = React.createClass({ 
    render: function() {
    	var divStyle = {
    		border: 'solid 1px black',
    		display: 'inline-block',
			padding: '5px'
    	};
        return (
            <div style={divStyle}>
                <SearchBox name="search" />
            </div>
        )
    }
});
module.exports = SearchContainer;