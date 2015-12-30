var AppDispatcher = require('../dispatcher/AppDispatcher');
var appConstants = require('../constants/appConstants');

var searchActions = {
	updateSearch: function(term) {
		AppDispatcher.handleActions({
			actionType: appConstants.UPDATE_SEARCH,
			data:term
		})
	}
};

module.exports = searchActions;