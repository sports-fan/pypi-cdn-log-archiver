import ConfigParser
import mimetypes

from boto.exception import S3ResponseError
from boto.s3.connection import S3Connection
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response, FileIter
from tomb_routes import simple_route


@simple_route("/{path:.*}")
def my_route(request, path):
    if not path:
        path = "/"

    if path.endswith("/"):
        path += "index.html"

    key = request.s3.get_key(path, validate=False)

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
    bucket_name = parser.get("docs-proxy", "aws_bucket")
    bucket = conn.get_bucket(bucket_name, validate=False)
    return bucket


parser = ConfigParser.RawConfigParser()
parser.read("config.ini")

config = Configurator()
config.registry.s3_conn = S3Connection(anon=True)
config.registry.config_parser = parser
config.add_request_method(_get_bucket, name="s3", reify=True)
config.scan()

application = config.make_wsgi_app()
