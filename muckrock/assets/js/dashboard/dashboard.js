import React from 'react';
import ReactDOM from 'react-dom';
import { Provider, connect } from 'react-redux';
import { getData } from './api';
import store from './store';
import rd3 from 'rd3';

function parseDate(string) {
    // date strings are formatted YYYY-MM-DD
    var year = parseInt(string.substring(0, 4));
    var month = parseInt(string.substring(5, 7)) - 1;
    var day = parseInt(string.substring(8, 10));
    var date = new Date(year, month, day);
    return date;
}

const Chart = React.createClass({
    collect: function(field) {
        // Collect just the data corresponding to a field
        return this.props.data.map(function(entry, index){
            return {
                date: parseDate(entry.fields['date']),
                data: entry.fields[field]
            }
        });
    },
    render: function() {
        const LineChart = rd3.LineChart;
        var data = this.collect(this.props.field);
        var chartData = [];
        if (data.length) {
            var chartData = [
                {
                    name: 'series1',
                    values: data.map(function(entry, index){
                        return {
                            x: entry.date,
                            y: entry.data,
                        }
                    }),
                }
            ];
        }
        return (
            <div className={this.props.field}>
                <LineChart
                    legend={false}
                    data={chartData}
                    width={600}
                    height={400}
                    title={this.props.title}
                    xAxisLabel='Date'
                />
            </div>
        );
    }
})

const DatePicker = React.createClass({
    render: function() {
        var min = this.props.dates.min.toDateString();
        var max = this.props.dates.max.toDateString();
        return (
            <div className="react-datepicker">
                <p>Min: {min}</p>
                <p>Max: {max}</p>
            </div>
        )
    }
});

const Loader = React.createClass({
    render: function() {
        return (
            <div className="loader">
                <div className="loader-inner line-scale-pulse-out-rapid">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
            </div>
        )
    }
});

const Dashboard = React.createClass({
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
        var data = this.props.data;
        return (
            <div className="charts">
                <Chart field="total_requests" title="Total Requests" data={this.props.data} />
                <Chart field="total_pages" title="Total Pages" data={this.props.data} />
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
                <DatePicker dates={this.props.dates} />
                {content}
            </div>
        )
    }
});

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
