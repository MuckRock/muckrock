import React from 'react';

import { getData } from '../api';

import { Chart } from './Chart';
import { DateRange } from './DateRange';
import { Value } from './Value';
import { Loader } from './Loader';

export const Dashboard = React.createClass({
    componentDidMount: function() {
        // Send min_date and max_date arguments as timestamps
        getData({
            'min_date': this.props.dates.min.toISOString(),
            'max_date': this.props.dates.max.toISOString(),
        });
    },
    renderLoading: function() {
        return <Loader />
    },
    renderError: function() {
        var error = this.props.error;
        return (
            <div className="error">
                <p className="error-code">{error.status}</p>
                <p className="error-message">{error.statusText}</p>
            </div>
        )
    },
    renderSuccess: function() {
        var data = this.props.data.results;
        return (
            <div className="charts">
                <Value field="total_requests" title="Total Requests" data={this.props.data} />
                <Chart field="total_requests" title="Total Requests" data={this.props.data} />
                <Value field="total_pages" title="Total Pages" data={this.props.data} />
                <Chart field="total_pages" title="Total Pages" data={this.props.data} />
                <Value field="total_users" title="Total Users" data={this.props.data} />
                <Chart field="total_users" title="Total Users" data={this.props.data} />
            </div>
        )
    },
    render: function() {
        var content;
        var className;
        if (this.props.loading) {
            content = this.renderLoading();
            className = 'loading';
        }
        else if (this.props.error != null) {
            content = this.renderError();
            className = 'error';
        }
        else {
            content = this.renderSuccess();
            className = '';
        }
        return (
            <div className={"dashboard " + className}>
                <DateRange dates={this.props.dates} />
                {content}
            </div>
        )
    }
});
