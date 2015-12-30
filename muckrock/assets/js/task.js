// Task.js
//
// Logic for client interactions with the MuckRock task system.

function authenticateAjax() {
    // Sets up authentication for AJAX transactions
    var csrftoken = $.cookie('csrftoken');
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
    }).ajaxError(function(event, response){
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
        success: null,
        dataType: 'json'
    });
}

/*
Need to add the action as a value since the button is being overridden.
In a non-JS form submission, the button would also include its value in the posted data.
*/

function resolve(taskForm) {
    var taskID = '#' + getTaskID($(taskForm).serializeArray()) + '-task';
    var taskData = $(taskForm).serialize() + '&resolve=true';
    var taskEndpoint = $(taskForm).attr('action');
    ajaxPost(taskID, taskEndpoint, taskData);
}

function reject(taskForm) {
    var taskID = '#' + getTaskID($(taskForm).serializeArray()) + '-task';
    var taskData = $(taskForm).serialize() + '&reject=true';
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
    $(task).addClass('resolved');
}

function formHasAction(taskForm, action) {
    // checks whether the task form has a 'Resolve' action or not
    var actionExists = false;
    var actionButton = 'button[name="' + action + '"]';
    if (!!$(taskForm).children(actionButton).length) {
        actionExists = true;
    }
    return actionExists;
}

function rebindCheckboxes(){
    // Rebinds the toggle all checkbox to only select checkboxes in task headers
    $('#toggle-all').off('click');
    $('#toggle-all').click(function(){
        var toggleAll = this;
        $('.task header :checkbox').not('#toggle-all').not('.list-filters-fields').each(function(){
            $(this).click(function(){
                toggleAll.checked = false;
            });
            if (!$(this).data('ignore-toggle-all')) {
                this.checked = toggleAll.checked;
                toggleBatchedButtons();
            }
        });
    });
}

////////////////////////////////////////////////////////////////////////////////

authenticateAjax();
rebindCheckboxes();

var tasks = $('.task');

// Hide all the resolved tasks
$('.resolved.task')
    .each(function(){
        markAsResolved(this);
    })
    .addClass('collapsed');

$('button[name="resolve"]').click(function(e){
    /* If the button clicked is the "resolve all" button, then get forms
    for all the currently checked tasks. Else, just get the form for the
    task that owns the button. */
    e.preventDefault();
    var forms = [];
    if ($(this).attr('id') == 'batched-resolve') {
        $(':checked[form=batched]').each(function() {
            var taskForm = $(this).closest('.task').find('form');
            // the form needs to have a resolve action in order to be added
            if (formHasAction(taskForm, 'resolve')) {
                forms.push(taskForm);
            }
        });
    } else {
        forms.push($(this).closest('form'));
    }
    $(forms).each(function(){
        resolve(this);
    });
    return false;
});

$('button[name="reject"]').click(function(e){
    e.preventDefault();
    var forms = [];
    if ($(this).attr('id') == 'batched-reject') {
        $(':checked[form=batched]').each(function() {
            var taskForm = $(this).closest('.task').find('form');
            if (formHasAction(taskForm, 'reject')) {
                forms.push(taskForm);
            }
        });
    } else {
        forms.push($(this).closest('form'));
    }
    $(forms).each(function(){
        console.log($(this));
        reject(this);
    });
    return false;
});

tasks.find('header').click(function() {
    $(this).parent().toggleClass('collapsed');
});

$('.task .permalink').click(function(e) {
    e.stopPropagation();
});

$('.task .checkbox').click(function(e) {
    e.stopPropagation();
});

var checkboxes = $('.task header').find(':checkbox');
var batchedButtons = $('#batched button').not('#collapse-all');
function toggleBatchedButtons() {
    if ($('.task header').find(':checkbox:checked').length > 0) {
        batchedButtons.attr('disabled', false);
    } else {
        batchedButtons.attr('disabled', true);
    }
}
batchedButtons.attr('disabled', true);
checkboxes.click(function(){
    toggleBatchedButtons();
});



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
