/* eslint no-undef: "off" */

var dashboard = new Dashboard();
var interval = 1000 * 60 * 5; // 5 minutes

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
dashboard.addWidget('processing_days_widget', 'Number', {
    getData: getData('processing_days_widget'),
    interval: interval
});
*/
dashboard.addWidget('processing_count_widget', 'Number', {
    getData: getData('processing_count_widget'),
    interval: interval
});
dashboard.addWidget('oldest_processing_widget', 'List', {
    getData: getData('oldest_processing_widget'),
    col: 1,
    row: 1,
    interval: interval
});
dashboard.addWidget('flag_graph_widget', 'Graph', {
    getData: getData('flag_graph_widget'),
    interval: interval
});
dashboard.addWidget('processing_graph_widget', 'Graph', {
    getData: getData('processing_graph_widget'),
    interval: interval
});
/*
dashboard.addWidget('flag_days_widget', 'Number', {
    getData: getData('flag_days_widget'),
    interval: interval
});
*/
dashboard.addWidget('flag_count_widget', 'Number', {
    getData: getData('flag_count_widget'),
    interval: interval
});
dashboard.addWidget('oldest_flag_widget', 'List', {
    getData: getData('oldest_flag_widget'),
    col: 1,
    row: 1,
    interval: interval
});
