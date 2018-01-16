/* eslint no-undef: "off" */

var dashboardSet = new DashboardSet({
  rollingChoices: true
});

var dashboardPF = dashboardSet.addDashboard('Processing/Flags');
var dashboardUser = dashboardSet.addDashboard('User');
var interval = 1000 * 60 * 5;
var topData = {};

function updateData(async) {
  Dashing.utils.get('top_widget', {
    success: function(data) {
      $.extend(topData, data);
    },
    async: async
  });
}

updateData(false);

setInterval(updateData, interval, true);

function getData(widgetName) {
  return function () {
    var data = topData[widgetName];
    if (data) {
      $.extend(this.scope, data);
      if (data.color) {
        $(this.getWidget()).css('background-color', data.color);
      }
    }
  };
}

dashboardPF.addWidget('processing_count_widget', 'Number', {
    getData: getData('ProcessingCountWidget'),
    interval: interval
});
dashboardPF.addWidget('oldest_processing_widget', 'List', {
    getData: getData('OldestProcessingWidget'),
    col: 1,
    row: 1,
    interval: interval
});
dashboardPF.addWidget('flag_graph_widget', 'Graph', {
    getData: getData('FlagGraphWidget'),
    interval: interval
});
dashboardPF.addWidget('processing_graph_widget', 'Graph', {
    getData: getData('ProcessingGraphWidget'),
    interval: interval
});
dashboardPF.addWidget('flag_count_widget', 'Number', {
    getData: getData('FlagCountWidget'),
    interval: interval
});
dashboardPF.addWidget('oldest_flag_widget', 'List', {
    getData: getData('OldestFlagWidget'),
    col: 1,
    row: 1,
    interval: interval
});
dashboardUser.addWidget('pro_user_graph_widget', 'Graph', {
    getData: getData('ProUserGraphWidget'),
    interval: interval
});
dashboardUser.addWidget('recent_requests_widget', 'List', {
    getData: getData('RecentRequestsWidget'),
    interval: interval
});
dashboardUser.addWidget('pro_user_count_widget', 'Number', {
    getData: getData('ProUserCountWidget'),
    interval: interval
});
dashboardUser.addWidget('requests_filed_widget', 'Number', {
    getData: getData('RequestsFiledWidget'),
    interval: interval
});
dashboardUser.addWidget('page_count_widget', 'Number', {
    getData: getData('PageCountWidget'),
    interval: interval
});
dashboardUser.addWidget('org_user_count_widget', 'Number', {
    getData: getData('OrgUserCountWidget'),
    interval: interval
});
