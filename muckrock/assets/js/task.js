/* Task.js
**
** Logic for client interactions with the MuckRock task system.
** Mostly involves submitting task forms via AJAX and handling successful responses.
*/

import Cookie from 'js-cookie';

function authenticateAjax() {
    // Sets up authentication for AJAX transactions
    var csrftoken = Cookie.get('csrftoken');
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
}

function ajaxPost(task, endpoint, data) {
    var pendingOverlay = $(task).children('.pending.overlay');
    var errorOverlay = $(task).children('.error.overlay');
    $(document).ajaxStart(function(){
        $(pendingOverlay).addClass('visible');
    }).ajaxError(function(){
        $(pendingOverlay).removeClass('visible');
        $(errorOverlay).addClass('visible');
        setTimeout(function(){
            $(errorOverlay).removeClass('visible');
        }, 3000);
        $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
    }).ajaxComplete(function(){
        $(pendingOverlay).removeClass('visible');
        markAsResolved(task);
        $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
    });
    $.ajax({
        url: endpoint,
        type: 'post',
        data: data,
        success: null
    });
}

/*
Need to add the action as a value since the button is being overridden.
In a non-JS form submission, the button would also include its value in the posted data.
*/

function batchAction(forms, action) {
    var taskID;
    var taskIDs = [];
    var taskData = {'tasks': []};
    taskData[action] = true;
    $(forms).each(function() {
        taskID = getTaskID($(this).serializeArray());
        taskIDs.push('#' + taskID + '-task');
        taskData['tasks'].push(taskID);
    });
    if (forms.length > 0) {
        var taskEndpoint = $(forms[0]).attr('action');
        ajaxPost(taskIDs.join(', '), taskEndpoint, taskData);
    }
}

function singleAction(taskForm, action) {
    var taskID = '#' + getTaskID($(taskForm).serializeArray()) + '-task';
    var taskData = $(taskForm).serialize() + '&' + action + '=true';
    var taskEndpoint = $(taskForm).attr('action');
    ajaxPost(taskID, taskEndpoint, taskData);
}

function getTaskID(taskFormData) {
    // Gets the task ID from a task form
    var taskID;
    $.each(taskFormData, function(i, input){
        if (input.name == 'task') {
            taskID = input.value;
        }
    });
    return taskID;
}

function markAsResolved(task) {
    $(task).addClass('green');
}

function formHasAction(taskForm, action) {
    // checks whether the task form has a 'Resolve' action or not
    var actionExists = false;
    var actionButton = 'button[name="' + action + '"]';
    if ($(taskForm).children(actionButton).length) {
        actionExists = true;
    }
    return actionExists;
}

function checkPdfExists(head_url, get_url) {
  $.ajax({
    url: head_url,
    type: 'head',
    success: function() {
      $('#snail-mail-bulk-download').text('Downloading');
      window.location.href = get_url;
    },
    error: function() {
      setTimeout(checkPdfExists, 5000, head_url, get_url);
    }
  });
}

////////////////////////////////////////////////////////////////////////////////

$('document').ready(function(){
  authenticateAjax();

  // Hide all the resolved tasks
  $('.resolved.task')
      .each(function(){
          markAsResolved(this);
      })
      .addClass('collapsed');

  /* TODO
  ** This should be rewritten to bind to the task's form submission event,
  ** not the form's resolve button click.
  */

  function ajaxSubmit(action) {
    return function(e) {
      /* If the button clicked is the "resolve all" button, then get forms
      for all the currently checked tasks. Else, just get the form for the
      task that owns the button. */
      e.preventDefault();
      var forms = [];
      if ($(this).attr('id') == 'batched-' + action) {
          $(':checked[form=batched]').each(function() {
              var taskForm = $(this).closest('.task').find('form');
              // the form needs to have a resolve action in order to be added
              if (formHasAction(taskForm, action)) {
                  forms.push(taskForm);
              }
          });
          batchAction(forms, action);
      } else {
          singleAction($(this).closest('form'), action);
      }
      return false;
    };
  }

  var actions = ['resolve', 'reject', 'spam', 'defer',
    'approve', 'save', 'move', 'no_mail'];
  for (var i = 0; i < actions.length; i++) {
    $('button[name="'+ actions[i] +'"]').click(ajaxSubmit(actions[i]));
  }

  var checkboxes = $('.task header').find(':checkbox');
  var batchedButtons = $('#batched button').not('#collapse-all');
  function toggleBatchedButtons() {
      if ($('.task header').find(':checked').length > 0) {
          batchedButtons.attr('disabled', false);
      } else {
          batchedButtons.attr('disabled', true);
      }
  }
  batchedButtons.attr('disabled', true);
  checkboxes.change(toggleBatchedButtons);

  $('#collapse-all').click(function(e){
      e.preventDefault();
      if ($(this).text() == "Collapse All") {
          $(this).text("Reveal All");
          $('.task').addClass('collapsed');
      } else {
          $(this).text("Collapse All");
          $('.task').removeClass('collapsed');
      }
  });

  $('.reveal-extra-context').click(function(e){
      e.preventDefault();
      if ($(this).data['state']) {
          // if on, turn off
          $(this).data['state'] = 0;
          $(this).text("More Info");
          $(this).next().addClass('hidden');
      } else {
          // if off, turn on
          $(this).data['state'] = 1;
          $(this).text("Less Info");
          $(this).next().removeClass('hidden');
      }
  });

  $('#snail-mail-bulk-download').click(function(){
    $(this).prop('disabled', 'disabled');
    $(this).text('Generating...');
    $.ajax({
      url: '/task/snail-mail/pdf/',
      data: window.location.search.substr(1),
      type: 'get',
      success: function(data) {
        checkPdfExists(data['head_url'], data['get_url']);
      },
      error: function() {
        $(this.text('Error!'));
      }
    });
  });

  $('select.assigned-chooser').change(function(){
    $.ajax({
      url: '/task/assign-to/',
      data: {
        task_pk: $(this).prop('name'),
        asignee: $(this).val()
      },
      type: 'post'
    });
  });

  // Defered loading of review agency tasks
  $(".review-agency-placeholder").each(function() {
    var id = $(this).data('id');
    var that = this;
    $.ajax({
      url: '/task/review-agency-ajax/' + id + '/',
      type: 'get',
      success: function(data) {
        $(that).html(data);
      },
      error: function() {
        $(that).html("<summary class='task__data'><p class='error'>Error</p></summary>");
      }
    });
  });

});
