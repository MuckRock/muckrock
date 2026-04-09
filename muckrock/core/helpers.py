# muckrock/core/tests/helpers.py
def get_404(client, url, **kwargs):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url, **kwargs)
    assert response.status_code == 404

    return response


# helper functions for view testing
def get_allowed(client, url, redirect=None, **kwargs):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url, follow=True, **kwargs)
    assert response.status_code == 200

    if redirect:
        assert response.redirect_chain == [("https://testserver:80" + redirect, 302)]

    return response


def post_allowed(client, url, data, redirect, **kwargs):
    """Test an allowed post with the given data and redirect location"""
    response = client.post(url, data, follow=True, **kwargs)
    assert response.status_code == 200
    assert response.redirect_chain == [(redirect, 302)]

    return response


def post_allowed_bad(client, url, templates, data=None, **kwargs):
    """Test an allowed post with bad data"""
    if data is None:
        data = {"bad": "data"}
    response = client.post(url, data, **kwargs)
    assert response.status_code == 200
    # make sure first 3 match (4th one might be form.html, not important
    assert [t.name for t in response.templates][:3] == templates + ["base.html"]


def get_post_unallowed(client, url, **kwargs):
    """Test an unauthenticated get and post on a url that is allowed
    to be viewed only by authenticated users"""
    redirect = "/accounts/login/?next=" + url
    response = client.get(url, **kwargs)
    assert response.status_code == 302
    assert response["Location"] == redirect
