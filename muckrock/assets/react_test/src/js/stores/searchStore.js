var AppDispatcher = require('../dispatcher/AppDispatcher');
var appConstants = require('../constants/appConstants');
var objectAssign = require('react/lib/Object.assign');
var EventEmitter = require('events').EventEmitter;

var CHANGE_EVENT = 'change';

var _store = {
	search: ''
}

var updateSearch = function(data) {
	_store.search = data.term;
}

var searchStore = objectAssign({}, EventEmitter.prototype, {
	addChangeListener: function(cb){
		this.on(CHANGE_EVENT, cb);
	},
	removeChangeListener: function(cb) {
		this.removeListener(CHANGE_EVENT, cb);
	},
	getSearch: function() {
		return _store;
	},
})

AppDispatcher.register(function(payload){
	var action = payload.action;
	switch(action.actionType){
		case appConstants.UPDATE_SEARCH:
			updateSearch(action.data);
			searchStore.emit(CHANGE_EVENT);
			break;
		default:
			return true;
	}
});

module.exports = searchStore;