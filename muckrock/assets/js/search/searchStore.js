import alt from './alt';
import SearchActions from './SearchActions';
import SearchSource from './SearchSource';

class SearchStore {
    constructor() {
        this.bindActions(SearchActions);
        this.registerAsync(SearchSource);
        this.data = {};
        this.query = ''
    }

    onSearch(query) {
    	this.setState({query: query})
        if (!this.getInstance().isLoading()) {
          this.getInstance().performSearch();
        }
    }

    onReceivedResults (data) {
    	console.log('received', data);
        this.setState({data: data});
    }

    onFetchingResultsFailed (response) {
    	console.log(response)
    }
}

export default alt.createStore(SearchStore, 'SearchStore');
