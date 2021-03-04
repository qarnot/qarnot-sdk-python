class PostRequest:
    def __init__(self, uri, body, args, kwargs):
        self.uri = uri
        self.body = body
        self.args = args
        self.kwargs = kwargs


class GetRequest:
    def __init__(self, uri):
        self.uri = uri


class MockResponse:
    def __init__(self, status_code, json=None):
        self.status_code = status_code
        self._json = json

    def json(self):
        return self._json


class MockConnection:
    def __init__(self):
        self.requests = []
        self._responses = []
        self.s3client = object()  # fake but must not be None


    def _post(self, url, json=None, *args, **kwargs):
        self.requests.append(PostRequest(url, json, args, kwargs))
        if len(self._responses) > 0:
            resp = self._responses[0]
            self._responses = self._responses[1:]
            return resp
        else:
            return MockResponse(200)


    def _get(self, url):
        self.requests.append(GetRequest(url))
        if len(self._responses) > 0:
            resp = self._responses[0]
            self._responses = self._responses[1:]
            return resp
        else:
            return MockResponse(200)

    def add_response(self, response):
        self._responses.append(response)
