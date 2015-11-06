var React = require('react');
var searchStore = require('./stores/searchStore');
var searchActions = require('./actions/searchActions');


var SearchBox = React.createClass({ 

	getInitialSate: function() {
		return {
			term: searchStore.getSearch()
		}
	},

	componentDidMount: function() {
		searchStore.addChangeListener(this._onChange);
	},

	componentWillUnmount: function() {
		searchStore.removeChangeListener(this._onChange);
	},

	_onChange: function() {
		this.setState({
			term: searchStore.getSearch()
		})
	},

	handleChange: function(event) {
		// this.setState({value: event.target.value});
		searchActions.updateSearch(event.target.value);
	},

    render: function() {
        return (
            <div>
                <span>{this.props.name}:</span><input type="text"  value={term} onChange={this.handleChange} />
            </div>
        )
    }
});

module.exports = SearchBox;