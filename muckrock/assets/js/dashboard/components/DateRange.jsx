import React from 'react';
import DatePicker from 'react-datepicker';
import moment from 'moment';

import { getData } from '../api';
import { setDates } from '../actions';
import store from '../store';

import 'react-datepicker/dist/react-datepicker.css';

export const DateRange = React.createClass({
    handleChange: function ({ startDate, endDate }) {
        startDate = startDate || this.props.dates.min;
        endDate = endDate || this.props.dates.max;
        if (moment(startDate).isAfter(endDate)) {
            var temp = startDate;
            startDate = endDate;
            endDate = temp;
        }
        store.dispatch(setDates(startDate, endDate));
        getData({
            'min_date': startDate.toISOString(),
            'max_date': endDate.toISOString(),
        });
    },
    handleChangeStart: function (startDate) {
        this.handleChange({ startDate })
    },
    handleChangeEnd: function (endDate) {
        this.handleChange({ endDate })
    },
    lastPeriod: function(period) {
        var startDate = moment().subtract(1, "days");
        var endDate = moment(startDate).subtract(1, period);
        this.handleChange({
            startDate: startDate.toDate(),
            endDate: endDate.toDate()
        });
    },
    handleLastWeek: function () {
        this.lastPeriod("weeks");
    },
    handleLastMonth: function () {
        this.lastPeriod("months");
    },
    handleLastYear: function () {
        this.lastPeriod("years");
    },
    handleForever: function() {
        var startDate = moment().subtract(1, "days");
        var endDate = moment('2010-01-01');
        this.handleChange({
            startDate: startDate.toDate(),
            endDate: endDate.toDate()
        });
    },
    render: function() {
        var min = moment(this.props.dates.min);
        var max = moment(this.props.dates.max);
        var yesterday = moment().subtract(1, "days");
        return (
            <div className="date-range">
                <div className="date-pickers">
                    <DatePicker
                        selected={min}
                        startDate={min}
                        endDate={max}
                        maxDate={yesterday}
                        showYearDropdown
                        onChange={this.handleChangeStart} />
                    <DatePicker
                        selected={max}
                        startDate={min}
                        endDate={max}
                        maxDate={yesterday}
                        showYearDropdown
                        onChange={this.handleChangeEnd} />
                </div>
                <div className="button-group">
                    <button className="button" onClick={this.handleLastWeek}>Last Week</button>
                    <button className="button" onClick={this.handleLastMonth}>Last Month</button>
                    <button className="button" onClick={this.handleLastYear}>Last Year</button>
                    <button className="button" onClick={this.handleForever}>Forever</button>
                </div>
            </div>
        );
    }
});
