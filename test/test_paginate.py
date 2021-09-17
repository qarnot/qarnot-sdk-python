#!/usr/bin/env python

from qarnot.pool import Pool
from qarnot.task import Task
from qarnot.exceptions import QarnotGenericException
from qarnot.job import Job
from qarnot import paginate
import pytest
import requests
import simplejson
from unittest.mock import Mock
from .mock_connection import MockConnection, PostRequest
from requests.models import Response


class TestPaginateResponseProperties:
    def test_the_paginate_response_properties(self):
        paginate_response = paginate.PaginateResponse(token="token",
                                                      next_token="next_token",
                                                      is_truncated=True,
                                                      page_data=["page_data"])
        assert paginate_response.token == "token"
        assert paginate_response.next_token == "next_token"
        assert paginate_response.is_truncated == True
        assert paginate_response.page_data == ["page_data"]
