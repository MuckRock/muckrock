/* ExemptionBrowserContainer.jsx
**
** Connects the ExemptionBrowser to the store.
*/

import ExemptionBrowser from '../components/ExemptionBrowser';
import { connect } from 'react-redux';
import axios from 'axios';

import {
    updateExemptionQuery,
    updateExemptionResults,
    displayExemptionDetail,
    displayExemptionList,
    displayExemptionForm,
    displayLoadingIndicator,
    resetExemptionState,
} from '../actions';

const exemptionSearchAPI = '/api_v1/exemption/search/';

const mapStateToProps = function(store) {
    return {
        exemptionQuery: store.exemptions.query,
        loadingResults: store.exemptions.loading,
        exemptionResults: store.exemptions.results,
        activeExemption: store.exemptions.exemption,
        formIsVisible: store.exemptions.formIsVisible,
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        searchExemptions: (query) => {
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
        displayExemptionDetail: (exemption) => {
            dispatch(displayExemptionDetail(exemption));
        },
        displayExemptionList: () => {
            dispatch(displayExemptionList());
        },
        displayExemptionForm: () => {
            dispatch(displayExemptionForm());
        }
    }
};

const ExemptionBrowserContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionBrowser)

export default ExemptionBrowserContainer
