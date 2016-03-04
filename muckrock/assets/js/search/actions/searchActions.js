import alt from '../alt';

class SearchActions { 
    constructor() {
        this.generateActions('search', 'receivedResults', 'fetchingResultsFailed');
    }
}

export default alt.createActions(SearchActions);