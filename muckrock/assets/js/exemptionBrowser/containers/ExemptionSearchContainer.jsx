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
    loadExemptionResults,
    resetExemptionState,
} from '../actions';

const exemptionSearchAPI = '/api_v1/exemption/search/';

// Get initial values for the search form
// Right now we need to pull them from the DOM,
// since we're only layering this React appliaction.
const jurisdictionId = $('#dom-data').data('jurisdiction');

const mapStateToProps = (store) => ({
    initialValues: {
        'q': store.exemptions.query,
        'jurisdiction': jurisdictionId
    }
});

const mapDispatchToProps = (dispatch) => ({
    onSubmit: (data) => {
        /*
        If the query is empty, then we reset the state of the exemption browser.
        Otherwise, we make a request to the exemption search endpoint.
        Once we get a response, we dispatch another action with the results of the search.
        */
        const q = data.q;
        if (q === undefined || q == '') {
            dispatch(resetExemptionState());
        } else {
            dispatch(loadExemptionResults());
            dispatch(updateExemptionQuery(q));
            axios.get(exemptionSearchAPI, {
                params: {
                    q: q,
                    jurisdiction: data.jurisdiction,
                }
            }).then(response => {
                const results = response.data.results;
                dispatch(updateExemptionResults(results));
            }).catch(error => {
                console.error(error);
            });
        }
    },
});

const ExemptionSearchContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionSearch);

export default ExemptionSearchContainer;
