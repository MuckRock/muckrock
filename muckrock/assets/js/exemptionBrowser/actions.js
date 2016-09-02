/* actions.js
**
** Exports actions for use by the exemption browser.
*/

import api from './api';

export const UPDATE_EXEMPTION_QUERY = 'UPDATE_EXEMPTION_QUERY';
export const UPDATE_EXEMPTION_RESULTS = 'UPDATE_EXEMPTION_RESULTS';
export const LOAD_EXEMPTION_RESULTS = 'LOAD_EXEMPTION_RESULTS';
export const UPDATE_VISIBILITY_FILTER = 'UPDATE_VISIBILITY_FILTER';
export const SELECT_EXEMPTION = 'SELECT_EXEMPTION';
export const RESET_EXEMPTION_STATE = 'RESET_EXEMPTION_STATE';

export const updateExemptionQuery = (query) => (
    {
        type: UPDATE_EXEMPTION_QUERY,
        query: query,
    }
);

export const updateExemptionResults = (results) => (
    {
        type: UPDATE_EXEMPTION_RESULTS,
        results: results,
    }
);

export const loadExemptionResults = () => (
    {
        type: LOAD_EXEMPTION_RESULTS,
    }
);

export const updateVisibilityFilter = (filter) => (
    {
        type: UPDATE_VISIBILITY_FILTER,
        filter: filter,
    }
);

export const selectExemption = (exemption) => (
    {
        type: SELECT_EXEMPTION,
        exemption: exemption,
    }
);

export const resetExemptionState = () => (
    {
        type: RESET_EXEMPTION_STATE,
    }
);

export const searchExemptions = (searchQuery) => {
    return (dispatch) => {
        dispatch(loadExemptionResults());
        dispatch(updateExemptionQuery(searchQuery.q));
        return api.get('exemption/', {
            params: searchQuery
        }).then(response => {
            const results = response.data.results;
            dispatch(updateExemptionResults(results));
        }).catch(error => {
            // TODO Handle errors by dispatching another action
            console.error(error);
        });
    }
};

export const submitExemption = (exemptionData) => {
    return api.post('exemption/submit/', exemptionData)
        .then(response => {
            // TODO Hanel successful submission
            console.debug('Posted successfully:', response);
        }).catch(error => {
            // TODO Handle submission error
            console.debug('Posted unsuccessfully:', error);
            if (error.response) {
              // The request was made, but the server responded with a status code
              // that falls out of the range of 2xx
              console.log(error.response.data);
              console.log(error.response.status);
              console.log(error.response.headers);
            } else {
              // Something happened in setting up the request that triggered an Error
              console.log('Error', error.message);
            }
            console.log(error.config);
        });
};
