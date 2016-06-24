import React from 'react';

import { getData } from '../api';

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
            <div className="values">
                <div className="values values--request">
                    <Value field="total_requests" title="Requests" data={this.props.data} grow={true} />
                    <Value field="total_pages" title="Pages" data={this.props.data} grow={true} />
                </div>
                <div className="values values--processing">
                    <Value field="total_requests_submitted" title="Processing" data={this.props.data} grow={false} />
                    <Value field="requests_processing_days" title="Total Days Processing" data={this.props.data} grow={false} />
                </div>
                <div className="values values--user">
                    <Value field="total_users" title="Users" data={this.props.data} grow={true} />
                    <Value field="pro_users" title="Pro Users" data={this.props.data} grow={true} />
                </div>
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
                <header className="dashboard__header">
                    <h1>Dashboard</h1>
                    <DateRange dates={this.props.dates} />
                </header>
                {content}
            </div>
        )
    }
});
