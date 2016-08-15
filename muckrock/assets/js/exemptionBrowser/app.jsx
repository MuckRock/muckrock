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

import ExemptionBrowser from './components/ExemptionBrowser';

/* First define the initial state, reducer, store, actions,
and use them to create the container component.*/

// We create the store and reducer in this file while it's still simple
// Later on, we should refactor these out.

const initialState = {query: ''}; // Dummy initial state
const rootReducer = function(state=initialState, action) {
    // Dummy reducer case: we'll fill this in later
    switch(action.type) {
        case 'EXEMPTION_SEARCH':
            const query = action.data.query;
            return Object.assign({}, state, {
                query: query
            });
    }
    return state;
};

const searchExemptions = (query) => (
    {
        type: 'EXEMPTION_SEARCH',
        data: {
            query: query,
        }
    }
);

// TODO We initialize the devtool here, but this should be removed in production settings
const devTool = window.devToolsExtension ? window.devToolsExtension() : undefined;
const store = createStore(rootReducer, initialState, devTool); // Create store from the root reducer

// More dummy values
const mapStateToProps = function(store) {
    return {exemptionQuery: store.query};
};
const mapDispatchToProps = (dispatch) => {
    return {
        onExemptionSearch: (query) => {
            dispatch(searchExemptions(query));
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
