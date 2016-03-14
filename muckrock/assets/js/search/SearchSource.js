import axios from 'axios';
import SearchActions from './SearchActions';

const SearchSource = {
    performSearch: {
        remote(state) {
            return axios.get('/search/', {
                params: {
                    q: state.query
                },
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
        },

        local() {
            return  null;
        },

        success: SearchActions.receivedResults,
        error: SearchActions.fetchingResultsFailed

    }
};

export default SearchSource;
