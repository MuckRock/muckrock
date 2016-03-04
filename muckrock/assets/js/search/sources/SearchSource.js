import axios from 'axios';
import SearchActions from '../actions/SearchActions';

const SearchSource = {
    performSearch: {
        remote(state) {
            return axios.get('/search/', {
                params: {
                    q: state.query
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