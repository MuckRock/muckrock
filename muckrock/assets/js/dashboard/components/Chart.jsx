import React from 'react';
var LineChart = require("react-chartjs").Line;

function parseDate(string) {
    // date strings are formatted YYYY-MM-DD
    var year = parseInt(string.substring(0, 4));
    var month = parseInt(string.substring(5, 7)) - 1;
    var day = parseInt(string.substring(8, 10));
    var date = new Date(year, month, day);
    return date;
}

export const Chart = React.createClass({
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
        var data = this.collect(this.props.field);
        var chartData = {
            labels: [],
            datasets: [
                {
                    label: this.props.label,
                    fill: true,
                    lineTension: 0.4,
                    pointColor: "rgba(72, 131, 207, 1)",
                    strokeColor: "rgba(72, 131, 207, 1)",
                    fillColor: "rgba(72, 131, 207, .5)",
                    data: []
                }
            ]
        };
        data.reverse().map(function(entry, index){
            chartData.labels.push(entry.date.toDateString());
            chartData.datasets[0].data.push(entry.data);
        });
        var chartOptions = {
            showScale: false,
            showTooltips: false,
            scaleGridLineColor: "rgba(255, 255, 255, .1)",
            scaleLineColor: "rgba(255, 255, 255, .1)",
            scaleShowVerticalLines: false,
            pointDot: false,
        }
        return (
            <LineChart data={chartData} options={chartOptions} width="150px" height="50px" />
        );
    }
});
