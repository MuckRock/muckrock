<section class="received message">
  <h1>Response</h1>
  <h2>{{task.date_created|date}}</h2>
  <span>Assigned to:</span>
  <form id="assign-{{task.pk}}" submit="{% url 'task-assign'%}">
    <select name="user" onchange="$.post('{% url "task-assign"%}', {user: $(this).val(), task: '{{task.pk}}'}, function (data) {$('#task-{{task.id}}-confirm').text(data).fadeIn().delay(2000).fadeOut()})">
      <option value="0">-None-</option>
      {% for user in staff_users %}
      <option value="{{user.pk}}" {% if task.assigned.pk == user.pk %}selected="selected"{%endif%}>{{user.username}}</option>
      {% endfor %}
    </select>
    <span id="task-{{task.id}}-confirm"></span>
  </form>
  {% with task.communication as comm %}
  <span>Response reseived from {{comm.priv_from_who}} for request {{comm.foia.title}} - {{comm.foia.mail_id}}</span><br />
  <form method="post">
    {% csrf_token %}
    <input type="hidden" name="task_pk" value="{{task.pk}}">
    <input type="hidden" name="task_class" value="responsetask">
    <select name="status">
      <option value="fix">Fix Required</option>
      <option value="payment">Payment Required</option>
      <option value="rejected">Rejected</option>
      <option value="no_docs">No Responsive Docs</option>
      <option value="done">Completed</option>
      <option value="partial">Partially Completed</option>
      <option value="abandoned">Withdrawn</option>
    </select>
    <input type="submit" name="submit" value="Set Status" class="button">
  </form>
  <span><a href="http://www.muckrock.com{% url 'admin:foia_foiarequest_change' comm.foia.pk %}">FOIA: {{comm.foia}}</a></span><br />
  <p>{{comm.communication}}</p>
  {% endwith %}
</section>
