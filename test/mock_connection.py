from qarnot.pool import Pool

class PostRequest:
    def __init__(self, uri, body, args, kwargs):
        self.uri = uri
        self.body = body
        self.args = args
        self.kwargs = kwargs


class PatchRequest:
    def __init__(self, uri, body, kwargs):
        self.uri = uri
        self.body = body
        self.kwargs = kwargs


class PutRequest:
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

def none_function(*arg, **kwarg):
    return None

class FakeS3:
    def create_bucket(self, Bucket):
        return True

class MockConnection:
    def __init__(self):
        self.requests = []
        self._responses = []
        self.s3client = FakeS3()  # fake but must not be None

    def _post(self, url, json=None, *args, **kwargs):
        self.requests.append(PostRequest(url, json, args, kwargs))
        if len(self._responses) > 0:
            resp = self._responses[0]
            self._responses = self._responses[1:]
            return resp
        else:
            return MockResponse(200)


    def _put(self, url, json=None, *args, **kwargs):
        self.requests.append(PutRequest(url, json, args, kwargs))
        if len(self._responses) > 0:
            resp = self._responses[0]
            self._responses = self._responses[1:]
            return resp
        else:
            return MockResponse(200)


    def _patch(self, url, json=None, **kwargs):
        self.requests.append(PatchRequest(url, json, kwargs))
        if len(self._responses) > 0:
            resp = self._responses[0]
            self._responses = self._responses[1:]
            return resp
        else:
            return MockResponse(200)


    def retrieve_pool(self, uuid):
        pool = Pool(self, "name", "profile", 2, "shortname")
        return pool

    def _get(self, url):
        self.requests.append(GetRequest(url))
        if len(self._responses) > 0:
            resp = self._responses[0]
            self._responses = self._responses[1:]
            return resp
        else:
            return MockResponse(200)

    def paginate_call(self, url, json=None, *args, **kwargs):
        return self._post(url, json, args, kwargs)

    def add_response(self, response):
        self._responses.append(response)
