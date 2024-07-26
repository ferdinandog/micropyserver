"""
MicroPyServer is a simple HTTP server for MicroPython projects.

@see https://github.com/troublegum/micropyserver

The MIT License

Copyright (c) 2019 troublegum. https://github.com/troublegum/micropyserver
Copyright (c) 2024 Ferdinando Grossi https://github.com/ferdinandog/micropyserver

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import re

""" HTTP response codes """
HTTP_CODES = {
    100: 'Continue',
    101: 'Switching protocols',
    102: 'Processing',
    200: 'Ok',
    201: 'Created',
    202: 'Accepted',
    203: 'Non authoritative information',
    204: 'No content',
    205: 'Reset content',
    206: 'Partial content',
    207: 'Multi status',
    208: 'Already reported',
    226: 'Im used',
    300: 'Multiple choices',
    301: 'Moved permanently',
    302: 'Found',
    303: 'See other',
    304: 'Not modified',
    305: 'Use proxy',
    307: 'Temporary redirect',
    308: 'Permanent redirect',
    400: 'Bad request',
    401: 'Unauthorized',
    402: 'Payment required',
    403: 'Forbidden',
    404: 'Not found',
    405: 'Method not allowed',
    406: 'Not acceptable',
    407: 'Proxy authentication required',
    408: 'Request timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length required',
    412: 'Precondition failed',
    413: 'Request entity too large',
    414: 'Request uri too long',
    415: 'Unsupported media type',
    416: 'Request range not satisfiable',
    417: 'Expectation failed',
    418: 'I am a teapot',
    422: 'Unprocessable entity',
    423: 'Locked',
    424: 'Failed dependency',
    426: 'Upgrade required',
    428: 'Precondition required',
    429: 'Too many requests',
    431: 'Request header fields too large',
    500: 'Internal server error',
    501: 'Not implemented',
    502: 'Bad gateway',
    503: 'Service unavailable',
    504: 'Gateway timeout',
    505: 'Http version not supported',
    506: 'Variant also negotiates',
    507: 'Insufficient storage',
    508: 'Loop detected',
    510: 'Not extended',
    511: 'Network authentication required',
}

""" File extension to MIME type """
MIME_TYPES = {
    'htm': 'text/html',
    'html': 'text/html',
    'txt': 'text/plain',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'json': 'application/json',
    'css': 'text/css',
    'ico': 'image/vnd.microsoft.icon',
    'js': 'text/javascript',
    'cjs': 'text/javascript',
    'vsg': 'image/svg+xml',
    'webp': 'image/webp',
    'map': 'application/octet-stream'
}

def send_response(server, response, http_code=200, content_type="text/html", extend_headers=None):
    """ send response """
    server.send("HTTP/1.0 " + str(http_code) + " " + HTTP_CODES.get(http_code) + "\r\n")
    server.send("Content-Type:" + content_type + "\r\n")
    if extend_headers is not None:
        for header in extend_headers:
            server.send(header + "\r\n")
    server.send("\r\n")
    server.send(response)


def send_binary_response(server, response, file_size, http_code=200, content_type="application/octet-stream", extend_headers=None):
    """ send response """
    server.send("HTTP/1.0 " + str(http_code) + " " + HTTP_CODES.get(http_code) + "\r\n")
    server.send("Content-Type:" + content_type + "\r\n")
    server.send("Content-Length:" + str(file_size) + "\r\n")
    if extend_headers is not None:
        for header in extend_headers:
            server.send(header + "\r\n")
    server.send("\r\n")
    server.send_binary(response)


def get_request_method(request):
    """ return http request method """
    lines = request.split("\r\n")
    return re.search("^([A-Z]+)", lines[0]).group(1)


def get_request_path(request):
    """ return http request path """
    lines = request.split("\r\n")
    return re.search("^[A-Z]+\\s+(/[-a-zA-Z0-9_.]*)*", lines[0]).group(1)


def get_request_query_string(request):
    """ return http request query string """
    lines = request.split("\r\n")
    match = re.search("\\?(.+)\\s", lines[0])
    if match is None:
        return ""
    else:
        return match.group(1)


def parse_query_string(query_string):
    """ return params from query string """
    if len(query_string) == 0:
        return {}
    query_params_string = query_string.split("&")
    query_params = {}
    for param_string in query_params_string:
        param = param_string.split("=")
        key = param[0]
        if len(param) == 1:
            value = ""
        else:
            value = param[1]
        query_params[key] = value
    return query_params


def get_request_query_params(request):
    """ return http request query params """
    query_string = get_request_query_string(request)
    return parse_query_string(query_string)


def get_request_post_params(request, expected_method='POST'):
    """ return params from POST or other specified type of request """
    request_method = get_request_method(request)
    if request_method != expected_method:
        return None
    return parse_query_string(get_request_body(request))


def get_request_body(request):
    """ return body from request """
    match = re.search("\r\n\r\n(.+)", request)
    if match is None:
        return {}
    query_string = match.group(1)
    return query_string


def unquote(string):
    """ unquote string """
    if not string:
        return ""

    if isinstance(string, str):
        string = string.encode("utf-8")

    bits = string.split(b"%")
    if len(bits) == 1:
        return string.decode("utf-8")

    res = bytearray(bits[0])
    append = res.append
    extend = res.extend

    for item in bits[1:]:
        try:
            append(int(item[:2], 16))
            extend(item[2:])
        except KeyError:
            append(b"%")
            extend(item)

    return bytes(res).decode("utf-8")
