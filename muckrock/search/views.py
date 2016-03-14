from django.views.generic import TemplateView
from django.http import HttpResponse

import json
import watson

class SearchView(TemplateView):
    """Get objects that correspond to the search query"""
    template_name = 'search.html'

    def __init__(self, *args, **kwargs):
        super(SearchView, self).__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Responds to AJAX requests with a JSON response"""
        if request.is_ajax():
            context = self.get_context_data(**kwargs)
            return self.render_to_json_response(context, **kwargs)
        else:
            return super(SearchView, self).get(request, *args, **kwargs)

    def get_query(self):
        """Returns the query"""
        return self.request.GET.get('q', '')

    def get_search_results(self, query):
        """Gets the query and perfoms the search."""
        return watson.search(query, )

    def render_to_json_response(self, context, **kwargs):
        """Serializes the search results into JSON"""
        # serialize the context
        json_context = json.dumps({
            "query": context['query'],
            "results": [
                {
                    "title": result.title,
                    "description": result.description,
                    "url": result.url,
                    "meta": result.meta,
                } for result in context['results']
            ]
        }).encode("utf-8")
        # Generate the response.
        response = HttpResponse(json_context, **kwargs)
        response["Content-Type"] = "application/json; charset=utf-8"
        response["Content-Length"] = len(json_context)
        return response

    def get_paginate_by(self):
        """Gets per_page the right way"""
        try:
            per_page = int(self.request.GET.get('per_page'))
            return max(min(per_page, 100), 5)
        except (ValueError, TypeError):
            return 25

    def get_context_data(self, **kwargs):
        """Returns the context"""
        context = super(SearchView, self).get_context_data(**kwargs)
        query = self.get_query()
        context['model'] = None
        context['query'] = query
        context['results'] = self.get_search_results(query)
        return context


class FOIASearchView(SearchView):
    pass
