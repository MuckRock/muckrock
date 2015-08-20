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

var tasks = $('.task');
var resolved = $('.resolved.task');

function resolve(taskForm) {
    taskID = '#' + getTaskID($(taskForm).serializeArray()) + '-task';
    taskData = $(taskForm).serialize() + '&resolve=true'
    console.log(taskData);
    $.ajax({
        type: 'POST',
        data: taskData,
        success: markAsResolved(taskID)
    });
}

function reject(taskForm) {
    taskData = $(taskForm).serializeArray()
    taskID = '#' + getTaskID(taskData) + '-task';
    console.log($(taskForm).serialize());
    console.log(taskID);
    $.ajax({
        type: 'POST',
        data: 'resolve=true&task=' + getTaskID(taskData),
        success: markAsResolved(taskID)
    });
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

function markAsResolved(taskID) {
    $(taskID).addClass('resolved');
    $(taskID).find(':input').attr('disabled', true).addClass('disabled');
    $(taskID).find('.task-type').text('Resolved');
}

resolved.each(function(){
    markAsResolved(this);
});

function formHasAction(taskForm, action) {
    // checks whether the task form has a 'Resolve' action or not
    var actionExists = false;
    var actionButton = 'button[name="' + action + '"]';
    if (!!$(taskForm).children(actionButton).length) {
        actionExists = true;
    }
    return actionExists;
}

$('button[name="resolve"]').click(function(e){
    e.preventDefault;
    // if the button clicked is the "resolve all" button,
    // then get forms for all the currently checked tasks
    // else,
    // just get the form for the task that owns the button
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
    e.preventDefault;
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

resolved.addClass('collapsed');
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
// Rebinds the toggle all checkbox to only select checkboxes in task headers
$('#toggle-all').unbind('click');
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
