import React from 'react';
import ReactDOM from 'react-dom';
import { Provider, connect } from 'react-redux';
import { getData } from './api';
import store from './store';

const Dashboard = React.createClass({
    componentDidMount: function() {
        getData();
    },
    render: function() {
        return (
            <div className="dashboard">
                <h1>Hello, World</h1>
            </div>
        )
    }
});

const mapStateToProps = function(store) {
    return {
        data: store.data
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
