from urllib.parse import urljoin, urlparse
from flask import request


def is_safe_redirect_target(target):
    if not target:
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme == host_url.scheme and redirect_url.netloc == host_url.netloc
