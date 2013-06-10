from traceback import print_exception
from StringIO import StringIO

from webob import Response

from pydap.lib import encode, __version__


class ErrorResponse(object):
    r"""
    A specialized response for errors.

    This is a special response used when an exception is captured and passed to
    the user as an Opendap error message:

    """
    def __init__(self, info):
        # get exception message
        buf = StringIO()
        print_exception(*info, file=buf)
        message = encode(buf.getvalue())

        # build error message
        code = getattr(info[0], 'code', -1)
        self.body = r'''Error {{
    code = {0};
    message = {1};
}}'''.format(code, message)

    def __call__(self, environ, start_response):
        res = Response()
        res.body = self.body
        res.status='500 Internal Error'
        res.content_type = 'text/plain'
        res.charset = 'utf-8'
        res.headers.add('Content-description', 'dods_error')
        res.headers.add('XDODS-Server', 'pydap/%s' % __version__)

        return res(environ, start_response)
