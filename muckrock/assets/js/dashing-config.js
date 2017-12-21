/* eslint no-undef: "off" */

var dashboardSet = new DashboardSet({
  rollingChoices: true
});

var dashboardPF = dashboardSet.addDashboard('Processing/Flags')
var dashboardUser = dashboardSet.addDashboard('User')
var interval = 1000 * 60 * 5;

function getData(widget_name) {
  return function () {
    var self = this;
    Dashing.utils.get(widget_name, function(data) {
      $.extend(self.scope, data);
      if (data.color) {
        $(self.getWidget()).css('background-color', data.color);
      }
    });
  };
}
/*
dashboardPF.addWidget('processing_days_widget', 'Number', {
    getData: getData('processing_days_widget'),
    interval: interval
});
*/
dashboardPF.addWidget('processing_count_widget', 'Number', {
    getData: getData('processing_count_widget'),
    interval: interval
});
dashboardPF.addWidget('oldest_processing_widget', 'List', {
    getData: getData('oldest_processing_widget'),
    col: 1,
    row: 1,
    interval: interval
});
dashboardPF.addWidget('flag_graph_widget', 'Graph', {
    getData: getData('flag_graph_widget'),
    interval: interval
});
dashboardPF.addWidget('processing_graph_widget', 'Graph', {
    getData: getData('processing_graph_widget'),
    interval: interval
});
/*
dashboardPF.addWidget('flag_days_widget', 'Number', {
    getData: getData('flag_days_widget'),
    interval: interval
});
*/
dashboardPF.addWidget('flag_count_widget', 'Number', {
    getData: getData('flag_count_widget'),
    interval: interval
});
dashboardPF.addWidget('oldest_flag_widget', 'List', {
    getData: getData('oldest_flag_widget'),
    col: 1,
    row: 1,
    interval: interval
});

dashboardUser.addWidget('pro_user_graph_widget', 'Graph', {
    getData: getData('pro_user_graph_widget'),
    interval: interval
});
dashboardUser.addWidget('recent_requests_widget', 'List', {
    getData: getData('recent_requests_widget'),
    interval: interval
});
dashboardUser.addWidget('pro_user_count_widget', 'Number', {
    getData: getData('pro_user_count_widget'),
    interval: interval
});
dashboardUser.addWidget('requests_filed_widget', 'Number', {
    getData: getData('requests_filed_widget'),
    interval: interval
});
dashboardUser.addWidget('page_count_widget', 'Number', {
    getData: getData('page_count_widget'),
    interval: interval
});
dashboardUser.addWidget('org_user_count_widget', 'Number', {
    getData: getData('org_user_count_widget'),
    interval: interval
});
