import React from 'react';
import ReactDOM from 'react-dom';

const Dashboard = React.createClass({
    render: function() {
        return (
            <div className="dashboard">
                <h1>Hello, World</h1>
            </div>
        )
    }
});

const selector = document.getElementById('dashboard');
if (selector) {
    ReactDOM.render(<Dashboard />, selector);
}
