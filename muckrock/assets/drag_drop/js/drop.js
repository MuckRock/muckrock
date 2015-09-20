/**
  basic drag and drop event-ery
  adapted from https://github.com/mikolalysenko/drag-and-drop-files
  so this is under an MIT license
**/

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
function drop(element, callback, enter, over) {
  element.addEventListener("dragenter", onDragEnter, false);
  element.addEventListener("dragleave", onDragLeave, false);
  element.addEventListener("dragover", onDragOver, false);
  element.addEventListener("drop", handleDrop.bind(undefined, callback), false);
}

module.exports = drop;
