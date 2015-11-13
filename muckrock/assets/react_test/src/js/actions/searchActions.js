var AppDispatcher = require('../dispatcher/AppDispatcher');
var appConstants = require('../constants/appConstants');

var searchActions = {
	updateSearch: function(search) {
		AppDispatcher.handleAction({
			actionType: appConstants.UPDATE_SEARCH,
			data:search
		})
	}
};

module.exports = searchActions;