document.addEventListener('DOMContentLoaded', function() {
    function updateArticlesField(inline) {
        var projectSelect = inline.querySelector('select[id$="-project"]');
        var articlesSelect = inline.querySelector('select[id$="-articles"]');
        if (!projectSelect || !articlesSelect) return;

        projectSelect.addEventListener('change', function() {
            var projectId = this.value;
            articlesSelect.innerHTML = '';
            if (projectId) {
                fetch('/admin/core/homepage/get-articles-for-project/?project_id=' + projectId)
                    .then(response => response.json())
                    .then(data => {
                        data.articles.forEach(function(article) {
                            var option = document.createElement('option');
                            option.value = article.id;
                            option.textContent = article.title;
                            articlesSelect.appendChild(option);
                        });
                    });
            }
        });
    }

    // Initial inlines
    document.querySelectorAll('.inline-related .form-row').forEach(function(inline) {
        updateArticlesField(inline);
    });

    // For newly added inlines (Django admin formset event)
    document.body.addEventListener('formset:added', function(event) {
        var inline = event.detail && event.detail.formsetName === 'featured_project_slots'
            ? event.detail.row
            : null;
        if (inline) {
            updateArticlesField(inline);
        }
    });
});