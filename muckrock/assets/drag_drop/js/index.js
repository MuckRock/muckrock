/**
 * npm and local dependencies.
**/

var qs = require("qs");
var FileReaderStream = require('filereader-stream'); // thank you @maxogden
var s3Stream = require('s3-upload-stream'); // thank you @nathanpeck
var AWS = require("aws-sdk"); // thank you @lsegal



/** previously drop.js */

function handleDrop(callback, event) {
  event.stopPropagation();
  event.preventDefault();
  hideTarget();
  // console.log("drop!")
  callback(Array.prototype.slice.call(event.dataTransfer.files))
}

// indicate it's active
function onDragEnter(event) {
  event.stopPropagation();
  event.preventDefault();
  showTarget();
  // console.log("enter!")
  return false;
}

function onDragLeave(event) {
  event.stopPropagation();
  event.preventDefault();
  // hideTarget();
  // console.log("leave!")
  return false;
}

// don't do anything while dragging
function onDragOver(event) {
  event.stopPropagation();
  event.preventDefault();
  // showTarget();
  // console.log("over!")
  return false;
}

var showTarget = function() {
  document.getElementById("dragging").style.display = "block";
};

var hideTarget = function() {
  document.getElementById("dragging").style.display = "none";
};

// set up callbacks on element
var drop = function (element, callback, enter, over) {
  element.addEventListener("dragenter", onDragEnter, false);
  element.addEventListener("dragleave", onDragLeave, false);
  element.addEventListener("dragover", onDragOver, false);
  element.addEventListener("drop", handleDrop.bind(undefined, callback), false);
}



/** previously utils.js **/

var Writable = require('stream').Writable;

var utils = {

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
      console.log("chunk received. encoding: " + encoding + ", length: " + chunk.length);
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

/**
 * Load in any state from the URL, and initialize bit vehicles.
**/

// initial load of parameters
var params = qs.parse(location.hash ? location.hash.replace("#", "") : null);

// session, can be changed throughout
var session = {
  key: params.key,
  "secret-key": params['secret-key'],
  bucket: params.bucket,
  public: params.public // "true" or "false"
};

session.bucket = $(".bucket").val();
session.key = $(".access-key").val();
session["secret-key"] = $(".secret-key").val();
session.public = false;

params.bucket = session.bucket;
params.key = session.key;
params["secret-key"] = session["secret-key"];
params.public = session.public;

// active upload
var active = {
  originalOffset: 0
};

// load offset as a number, cache the starting offset for this session.
// if (params.offset) params.offset = parseInt(params.offset);
// var originalOffset = params.offset || 0;

// configure AWS
var awsClient;
function initAWS() {
  AWS.config.update({
    accessKeyId: session.key,
    secretAccessKey: session["secret-key"]
  });
  awsClient = new AWS.S3();
}
initAWS();
s3Stream.client(awsClient);

var fstream;
var upload;
var log = utils.log("main-log");


/**
 * Initialize destination parameters.
*/

/*
$(".bucket").val(params.bucket);
$(".access-key").val(params.key);
$(".secret-key").val(params['secret-key']);
$("#public").prop("checked", (params.public == "false" ? false : true));
*/

// changing values updates session automatically
$(".param").keyup(function() {
  console.log("changed value.");
  session.bucket = $(".bucket").val();
  session.key = $(".access-key").val();
  session["secret-key"] = $(".secret-key").val();
  initAWS();
});

$("#public").click(function() {
  console.log("changed permissions, public: " + permissions());
  session.public = permissions().toString();
});

// S3 credentials testing
$(".s3.test").click(function() {
  $(".s3-test").hide();
  $(".s3-test.loading").show();

  awsClient.listObjects({Bucket: session.bucket}, function(err, objects) {
    $(".s3-test").hide();
    if (err) {
      if (err.name == "NetworkingError")
        $(".s3-test.cors").show();
      else
        $(".s3-test.credentials").show();
    } else {
      $(".s3-test").hide();
      $(".s3-test.success").show();
    }
  });
});

/**
 * Has the user said the file can be publicly downloadable?
 */
function permissions() {
  return $("#public").prop("checked");
};


/** manage file and AWS streams */

var uploadFile = function(file) {

  /**
  * Create the file reading stream.
  **/

  fstream = FileReaderStream(file, {
    chunkSize: (1 * 1024 * 1024),
    offset: params.offset
  });

  // log MBs read to dev console
  fstream.on('progress', utils.mbCounter());
  fstream.on('progress', function(progress) {
    var pct = Math.floor((progress/file.size) * 100);
    $(".progress .reading").css("width", pct + "%");
  });

  fstream.on('pause', function(offset) {
    console.log("filereader-stream: PAUSE at " + offset);
  });

  fstream.on('resume', function(offset) {
    console.log("filereader-stream: RESUME at " + offset);
  });

  fstream.on('end', function(size) {
    console.log("filereader-stream: END at " + size);
    $(".progress .reading").css("width", "100%");
  });

  fstream.on('error', function(err, data) {
    console.log(err);
  })

  params.filename = file.name;


  /**
  * Create the upload stream.
  **/

  upload = new s3Stream.upload({
    "Bucket": params.bucket,
    "Key": "scans/" + file.name,
    "ContentType": file.type,
    "ACL": (permissions() ? "public-read" : "private")
  });

  // for later fetching, even if the user checked/unchecked the box during the upload
  upload.public = permissions();

  // by default, part size means a 50GB max (10000 part limit)
  // by raising part size, we increase total capacity
  if (file.size > (50 * 1024 * 1024 * 1024)) {
    var newSize = parseInt(file.size / 9500);
    upload.maxPartSize(newSize); // 9500 for buffer
    log("Will be uploading " + utils.display(newSize) + " chunks to S3.");
    console.log("Part size should be: " + newSize);
  } else {
    upload.maxPartSize(5 * 1024 * 1024);
  }

  // 1 at a time for now
  upload.concurrentParts(1);

  upload.on('part', function(data) {
    var progress = active.originalOffset + data.uploadedSize;
    var pct = Math.floor((progress/file.size) * 100);

    var parts = Math.ceil(file.size / upload.getMaxPartSize());
    log("Uploaded part " + data.PartNumber + "/" + parts + ", " + utils.display(progress) + "/" + utils.display(file.size) + " (" + pct + "%).");
    console.log("s3-upload-stream: PART " + data.PartNumber + " / " + parts);

    $(".progress .voyage").css("width", pct + "%");
  });

  upload.on('uploaded', function(data) {
    var download = "Arrived! ";

    if (upload.public) {
      download += "Download <strong>" + file.name + "</strong> at " +
        "<a target=\"_blank\" href=\"" + data.Location + "\">" +
          data.Location +
        "</a>";
    } else {
      download += file.name + " has been uploaded privately as " +
        " <strong>" + data.Key + "</strong>.";
    }

    log(download);

    $(".control").hide();

    console.log("s3-upload-stream: UPLOADED.");
  });

  upload.on('error', function(err) {
    log("Error uploading file: " + err);
    console.log("s3-upload-stream: ERROR, " + err);
  });

  upload.on('ready', function(uploadId) {
    console.log("s3-upload-stream: READY, upload ID created.");
    log("Upload initiated, beginning to transfer parts.")

    $(".control.pause").show();
  });

  upload.on('pausing', function(pending) {
    console.log("s3-upload-stream: PAUSING, " + pending + " parts in the air.")
    log("<strong>Pausing download, do not close tab</strong>, still " + pending + " " + utils.display(upload.getMaxPartSize()) + " part(s) waiting to finish uploading.")
  });

  upload.on('paused', function(data) {
    console.log("s3-upload-stream: PAUSED. uploadId: " + data.UploadId + ", parts: " + data.Parts.length + ", uploaded: " + data.Uploaded);
    log("OK, fully paused.");

    // switch indicator
    $(".control").hide();
    $(".control.resume").show();

    // the Uploaded value will be relative to the creation of this stream
    // instance, so needs to be based off offset from before the stream
    // instance was created.
    params.offset = active.originalOffset + data.Uploaded;
    params.UploadId = data.UploadId;
    params.Parts = data.Parts;
  });

  upload.on('resume', function() {
    console.log("s3-upload-stream: RESUMED.");
  });

  // begin the voyage
  log("<strong>" + file.name + "</strong> is embarking on a " + utils.display(file.size) + " voyage.")
  $(".progress .voyage, .progress .reading").css("width", "0%");
  $(".control").hide();

  fstream.pipe(upload);
  // fstream.pipe(utils.echo())
};


// S3 pause/resume - the user's pause/resume
$(".control.pause").click(function() {
  if (upload){
    upload.pause();
    $(".control").hide();
    $(".control.pausing").show();
  }
  return false;
});

$(".control.resume").click(function() {
  if (upload) {
    upload.resume();
    $(".control").hide();
    $(".control.pause").show();
  }
  return false;
});


drop(document.body, function(files) {if (files[0]) uploadFile(files[0]);});
console.log("Drop target armed.")
