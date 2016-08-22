/* ExemptionSearchContainer.jsx
**
** Connects the exemption state and actions to the search component.
*/

import axios from 'axios';
import { connect } from 'react-redux';

import ExemptionSearch from '../components/ExemptionSearch';
import {
    updateExemptionQuery,
    updateExemptionResults,
    displayLoadingIndicator,
    resetExemptionState,
} from '../actions';

const exemptionSearchAPI = '/api_v1/exemption/search/';

const mapStateToProps = (store) => ({
    query: store.exemptions.query,
});

const mapDispatchToProps = (dispatch) => ({
    onSubmit: (query) => {
        /*
        If the query is empty, then we reset the state of the exemption browser.
        Otherwise, we make a request to the exemption search endpoint.
        Once we get a response, we dispatch another action with the results of the search.
        */
        if (query == '') {
            dispatch(resetExemptionState());
        } else {
            dispatch(displayLoadingIndicator());
            dispatch(updateExemptionQuery(query));
            axios.get(exemptionSearchAPI, {
                params: {
                    q: query
                }
            }).then(response => {
                const results = response.data.results;
                dispatch(updateExemptionResults(results));
            });
        }
    },
});

const ExemptionSearchContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionSearch);

export default ExemptionSearchContainer;
