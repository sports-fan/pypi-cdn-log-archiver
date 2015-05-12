import mimetypes
import os

from boto.exception import S3ResponseError
from boto.s3.connection import S3Connection
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPMovedPermanently, HTTPNotFound
from pyramid.response import Response, FileIter
from tomb_routes import simple_route


@simple_route("/{path:.*}")
def my_route(request, path):
    if not path:
        path = "/"

    if path.endswith("/"):
        path += "index.html"

    try:
        key = request.s3.get_key(path)
    except S3ResponseError:
        # Try the same request, but with a /index.html added onto it.
        key = request.s3.get_key(path + "/index.html")
        return HTTPMovedPermanently("/" + path + "/")

    try:
        data = key.read()
    except S3ResponseError:
        return HTTPNotFound()

    content_type, content_encoding = mimetypes.guess_type(path)

    return Response(data,
        content_type=content_type,
        content_encoding=content_encoding,
    )


def _get_bucket(request):
    conn = request.registry.s3_conn
    bucket = conn.get_bucket(request.registry.s3_bucket, validate=False)
    return bucket


config = Configurator()
config.registry.s3_conn = S3Connection(anon=True)
config.registry.s3_bucket = os.environ["DOCS_PROXY_BUCKET"]
config.add_request_method(_get_bucket, name="s3", reify=True)
config.scan()

application = config.make_wsgi_app()
