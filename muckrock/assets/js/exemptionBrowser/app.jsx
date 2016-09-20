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
import { combineReducers, createStore, applyMiddleware } from 'redux';
import thunk from 'redux-thunk';
import { Provider } from 'react-redux';
import { reducer as formReducer } from 'redux-form';

import exemptionReducer from './reducer'
import ExemptionBrowserContainer from './containers/ExemptionBrowserContainer';


const reducer = combineReducers({
    exemptions: exemptionReducer,
    form: formReducer,
});
const devTool = window.devToolsExtension ? window.devToolsExtension() : undefined;
const store = createStore(
    reducer,
    devTool,
    applyMiddleware(thunk)
); // Create store from the root reducer

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
