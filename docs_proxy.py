import ConfigParser
import mimetypes

import fs.errors
import fs.s3fs
import fs.wrapfs.readonlyfs

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

    try:
        data = request.fs.getcontents(path, mode="rb")
    except fs.errors.ResourceNotFoundError:
        return HTTPNotFound()

    content_type, content_encoding = mimetypes.guess_type(path)

    return Response(data,
        content_type=content_type,
        content_encoding=content_encoding,
    )


parser = ConfigParser.RawConfigParser()
parser.read("config.ini")

config = Configurator()
config.registry.fs = fs.wrapfs.readonlyfs.ReadOnlyFS(
    fs.s3fs.S3FS(
        bucket=parser.get("docs-proxy", "aws_bucket"),
        aws_access_key=parser.get("docs-proxy", "aws_access_key_id"),
        aws_secret_key=parser.get("docs-proxy", "aws_secret_access_key"),
    ),
)
config.add_request_method(
    lambda request: request.registry.fs,
    name="fs", reify=True,
)
config.scan()

application = config.make_wsgi_app()
