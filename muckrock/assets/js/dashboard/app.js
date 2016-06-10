import React from 'react';
import ReactDOM from 'react-dom';
import { Provider, connect } from 'react-redux';

import store from './store';

import { Dashboard } from './components/Dashboard';

const mapStateToProps = function(store) {
    return {
        loading: store.loading,
        data: store.data,
        error: store.error,
        dates: store.dates
    };
};

const DashboardContainer = connect(mapStateToProps)(Dashboard);

const selector = document.getElementById('dashboard');
if (selector) {
    ReactDOM.render(
        (
            <Provider store={store}>
                <DashboardContainer />
            </Provider>
        ),
        selector
    );
}
