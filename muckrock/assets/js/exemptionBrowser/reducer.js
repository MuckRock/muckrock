/* reducer.js
**
** The reducer contains logic on how to mutate the state in response
** to a dispatched action.
*/

import {
    UPDATE_VISIBILITY_FILTER,
    UPDATE_EXEMPTION_QUERY,
    UPDATE_EXEMPTION_RESULTS,
    LOAD_EXEMPTION_RESULTS,
    SELECT_EXEMPTION,
    SUBMIT_EXEMPTION,
    RESET_EXEMPTION_STATE
} from './actions';

export const ExemptionVisibilityFilters = {
    SHOW_SEARCH: 'SHOW_SEARCH',
    SHOW_DETAIL: 'SHOW_DETAIL',
    SHOW_FORM: 'SHOW_FORM',
    SHOW_ERROR: 'SHOW_ERROR'
};

const initialState = {
    query: null,
    loading: false,
    results: [],
    exemption: null,
    filter: 'SHOW_SEARCH',
    submission_form: {
        state: 'DEFAULT',
        response: null
    }
};

const exemptionReducer = function(state=initialState, action) {
    switch(action.type) {
        case UPDATE_VISIBILITY_FILTER:
            return Object.assign({}, state, {
                filter: action.filter
            });
        case UPDATE_EXEMPTION_QUERY:
            return Object.assign({}, state, {
                query: action.query
            });
        case UPDATE_EXEMPTION_RESULTS:
            return Object.assign({}, state, {
                results: action.results,
                loading: false
            });
        case LOAD_EXEMPTION_RESULTS:
            return Object.assign({}, state, {
                loading: true
            });
        case SELECT_EXEMPTION:
            return Object.assign({}, state, {
                exemption: action.exemption
            });
        case SUBMIT_EXEMPTION:
            switch(action.state) {
                case 'LOADING':
                    return Object.assign({}, state, {
                        submission_form: {
                            state: 'LOADING'
                        }
                    });
                case 'SUCCESS':
                    return Object.assign({}, state, {
                        submission_form: {
                            state: 'SUCCESS',
                            response: action.response
                        }
                    });
                case 'FAILURE':
                    return Object.assign({}, state, {
                        submission_form: {
                            state: 'FAILURE',
                            response: action.response
                        }
                    });
                default:
                    return Object.assign({}, state, {
                        submission_form: {
                            state: 'DEFAULT',
                            response: null
                        }
                    });
            }
        case RESET_EXEMPTION_STATE:
            return Object.assign({}, state, initialState);
        default:
            return state;
    }
};

export default exemptionReducer;
