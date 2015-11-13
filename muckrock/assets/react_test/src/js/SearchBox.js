var React = require('react');
var searchStore = require('./stores/searchStore');
var searchActions = require('./actions/searchActions');


var SearchBox = React.createClass({ 

	getInitialState: function() {
		return {
			search: searchStore.getSearch()
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
		console.log(searchStore.returnSearchURL());
	},

	handleChange: function(event) {
		// this.setState({value: event.target.value});
		searchActions.updateSearch(event.target.value);
	},

    render: function() {
    	console.log(this.state);
        return (
            <div>
                <span>{this.props.name}:</span><input type="text"  value={this.state.search} onChange={this.handleChange} />
            </div>
        )
    }
});

module.exports = SearchBox;