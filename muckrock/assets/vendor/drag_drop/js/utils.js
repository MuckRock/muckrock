var Writable = require('stream').Writable;

module.exports = {

  updateLink: function(qs, params) {
    var link = window.location.protocol + "//" + window.location.host + "/#" + qs.stringify(params);
    window.location = link;
    return false;
  },

  echo: function(delay) {
    var echoStream = new Writable({
      highWaterMark: 4194304
    });

    echoStream._write = function (chunk, encoding, next) {
      console.log("chunk received. " + chunk.length);
      setTimeout(next, delay);
    };

    return echoStream;
  },

  display: function(bytes) {
    if (bytes > 1e9)
      return (bytes / 1e9).toFixed(2) + 'GB';
    else if (bytes > 1e6)
      return (bytes / 1e6).toFixed(2) + 'MB';
    else
      return (bytes / 1e3).toFixed(2) + 'KB';
  },

  // counter of MBs
  mbCounter: function() {
    var MBs = 5;
    var MB = 1000 * 1000;
    var next = 1;
    return function(progress) {
      if (progress > (next * (MBs * MB))) {
        var current = parseInt(progress / (MBs * MB)) * MBs;
        console.log("filereader-stream: MBs: " + current);
        next = parseInt((current + MBs) / MBs);
      }
    }
  },

  log: function(id) {
    var elem = document.getElementById(id);

    return function(msg) {
      elem.innerHTML = (msg + "<br/>") + elem.innerHTML;
      elem.scrollTop = 0; // elem.scrollHeight; // for bottom
    }
  }

};
