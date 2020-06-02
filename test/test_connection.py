#!/usr/bin/env python

import qarnot
import pytest
import requests
import simplejson

class TestConnectionMethods:
    def test_connection_with_bad_ssl_return_the_good_exception(self):
        with pytest.raises(requests.exceptions.SSLError):
            assert qarnot.Connection(cluster_url="https://expired.badssl.com", client_token="token")

    def test_connection_with_bad_ssl_and_uncheck_return_JSONDecodeError_exception(self):
        with pytest.raises(simplejson.errors.JSONDecodeError):
            assert qarnot.Connection(cluster_url="https://expired.badssl.com", client_token="token", cluster_unsafe=True)
