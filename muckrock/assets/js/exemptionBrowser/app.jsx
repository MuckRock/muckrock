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

const initialState = {foo: 1}; // Dummy initial state
const rootReducer = function(state=initialState, action) {
    // Dummy reducer case: we'll fill this in later
    switch(action.type) {
        case 'FOO_UP':
            const moreFoo = state.foo + 1
            return Object.assign({}, state, {
                foo: moreFoo
            })
        case 'FOO_DOWN':
            const lessFoo = state.foo - 1
            return Object.assign({}, state, {
                foo: lessFoo
            })
    }
    return state;
};

// We create a dummy action to make sure actions work right!

const incrementFoo = () => (
    {type: 'FOO_UP'}
);
const decrementFoo = () => (
    {type: 'FOO_DOWN'}
)

// TODO We initialize the devtool here, but this should be removed in production settings
const devTool = window.devToolsExtension ? window.devToolsExtension() : undefined;
const store = createStore(rootReducer, initialState, devTool); // Create store from the root reducer

// More dummy values
const mapStateToProps = function(store) {
    return {foo: store.foo};
};
const mapDispatchToProps = (dispatch) => {
    return {
        onIncrementClick: () => {
            dispatch(incrementFoo());
        },
        onDecrementClick: () => {
            dispatch(decrementFoo());
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
