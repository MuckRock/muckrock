/* reducer.js
**
** The reducer contains logic on how to mutate the state in response
** to a dispatched action.
*/

const initialState = {
    query: '',
    loading: false,
    results: [],
    exemption: null,
    formIsVisible: false,
};

const exemptionReducer = function(state=initialState, action) {
    switch(action.type) {
        case 'UPDATE_EXEMPTION_QUERY':
            return Object.assign({}, state, {
                query: action.query
            });
        case 'UPDATE_EXEMPTION_RESULTS':
            return Object.assign({}, state, {
                results: action.results,
                loading: false,
            });
        case 'DISPLAY_LOADING_INDICATOR':
            return Object.assign({}, state, {
                loading: true,
            });
        case 'DISPLAY_EXEMPTION_DETAIL':
            return Object.assign({}, state, {
                exemption: action.exemption
            });
        case 'DISPLAY_EXEMPTION_LIST':
            return Object.assign({}, state, {
                exemption: null,
                formIsVisible: false,
                loading: false,
            });
        case 'DISPLAY_EXEMPTION_FORM':
            return Object.assign({}, state, {
                formIsVisible: true
            });
        case 'RESET_EXEMPTION_STATE':
            return Object.assign({}, state, initialState);
    }
    return state;
};

export default exemptionReducer;
