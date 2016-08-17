/* app.jsx
**
** This is the starting point for the Exemption Browser microapp.
** It provides a way for users to search and reference exemptions when composing an appeal.
**
** This is the first instance of React we are adding to MuckRock for production.
** There's no guarantee that it'll be structured perfectly.
** It'll probably need to be refactored a bunch.
** Tests should be written against it, also.
*/

import React from 'react';
import { render } from 'react-dom';
import { createStore } from 'redux';
import { Provider, connect } from 'react-redux';
import axios from 'axios';

import ExemptionBrowser from './components/ExemptionBrowser';
import {
    updateExemptionQuery,
    updateExemptionResults,
    displayExemptionDetail,
    displayExemptionList,
    displayExemptionForm,
    displayLoadingIndicator,
    resetExemptionState,
} from './actions';

/* First define the initial state, reducer, store, actions,
and use them to create the container component.*/

// We create the store and reducer in this file while it's still simple
// Later on, we should refactor these out.

const exemptionSearchAPI = '/api_v1/exemption/search/';

const initialState = {
    query: '',
    loading: false,
    results: [],
    exemption: null,
    formIsVisible: false,
};

const rootReducer = function(state=initialState, action) {
    // Dummy reducer case: we'll fill this in later
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

// TODO We initialize the devtool here, but this should be removed in production settings
const devTool = window.devToolsExtension ? window.devToolsExtension() : undefined;
const store = createStore(rootReducer, initialState, devTool); // Create store from the root reducer

const mapStateToProps = function(store) {
    return {
        exemptionQuery: store.query,
        loadingResults: store.loading,
        exemptionResults: store.results,
        activeExemption: store.exemption,
        formIsVisible: store.formIsVisible,
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
}
const ExemptionBrowserContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionBrowser);

/* Next we render the component onto the selected element */

const exemptionBrowserSelector = document.getElementById('exemptionBrowser');
// prevent rendering onto an unidentified value
if (exemptionBrowserSelector) {
    render((
        <Provider store={store}>
            <ExemptionBrowserContainer />
        </Provider>
    ), exemptionBrowserSelector);
}

/* Now we should have the React app working! */
