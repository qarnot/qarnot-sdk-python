#!/usr/bin/env python

import qarnot
import pytest
from unittest import TestCase
from unittest.mock import patch, Mock, PropertyMock
import requests
import simplejson

expected_or_tags_filter = {"operator": "Or", "filters":[{"operator": "Equal", "field": "Tags", "value": "tag1"}, {"operator": "Equal", "field": "Tags", "value": "tag2"}]}
expected_and_tags_filter = {"operator": "And", "filters":[{"operator": "Equal", "field": "Tags", "value": "tag_inter1"}, {"operator": "Equal", "field": "Tags", "value": "tag_inter2"}]}
expected_and_or_tags_filter = {"operator": "And", "filters": [
            {"operator": "Or", "filters": [{"operator": "Equal", "field": "Tags", "value": "tag1"}, {
                "operator": "Equal", "field": "Tags", "value": "tag2"}]},
            {"operator": "And", "filters": [{"operator": "Equal", "field": "Tags", "value": "tag_inter1"}, {
                "operator": "Equal", "field": "Tags", "value": "tag_inter2"}]}
        ]}

class TestConnectionMethods(TestCase):
    @pytest.mark.slow
    def test_connection_with_bad_ssl_return_the_good_exception(self):
        with pytest.raises(requests.exceptions.SSLError):
            assert qarnot.Connection(cluster_url="https://expired.badssl.com", client_token="token")

    @pytest.mark.slow
    def test_connection_with_bad_ssl_and_uncheck_return_JSONDecodeError_exception(self):
        with pytest.raises(simplejson.errors.JSONDecodeError):
            assert qarnot.Connection(cluster_url="https://expired.badssl.com", client_token="token", cluster_unsafe=True)

class TestConnectionPaginateMethods():
    @patch("qarnot.connection.Connection._get")
    def get_connection(self, mock_get):
        mock_get.return_value.status_code = 200
        connec = qarnot.Connection(
            client_token="token", cluster_url="https://localhost", storage_url="https://localhost")
        return connec

    def test_profiles_names(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = ["test1", "test2"]
            retriever = connec.profiles_names()
            assert "/profiles" == mock_get.call_args[0][0]
            assert retriever[0] == "test1" and retriever[1] == "test2"

    def test_profiles(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.profiles_names") as mock_names:
            with patch("qarnot.connection.Connection._get") as mock_get:
                mock_names.return_value = ["hello01", "hello02", "hello03", "hello04", "hello05", "hello06", "hello07", "hello08", "hello09", "hello10", "hello11", "hello12", "hello13"]
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"name":"world",
                                                           "constants": [{"name": "foo", "value": "bar"}, {"name": "foo2", "value": "bar2"}]}
                retriever = connec.profiles()
                assert len(retriever) == 13
                for ret in retriever:
                    assert ret.name == "world" and ret.constants == (('foo', 'bar'),('foo2', 'bar2'))
                for arg in mock_get.call_args_list:
                    assert arg[0][0].startswith("/profiles/hello")

    def test_profiles_with_internal_server_error(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.profiles_names") as mock_names:
            with patch("qarnot.connection.Connection._get") as mock_get:
                mock_names.return_value = ["hello01", "hello02", "hello03", "hello04", "hello05", "hello06", "hello07", "hello08", "hello09", "hello10", "hello11", "hello12", "hello13"]
                mock_get.return_value.status_code = 503
                mock_get.return_value.json.return_value = {"name":"world",
                                                           "constants": [{"name": "foo", "value": "bar"}, {"name": "foo2", "value": "bar2"}]}
                with pytest.raises(qarnot.QarnotGenericException):
                    retriever = connec.profiles()

    def test_profiles_with_not_found_error(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.profiles_names") as mock_names:
            with patch("qarnot.connection.Connection._get") as mock_get:
                mock_names.return_value = ["hello01", "hello02", "hello03", "hello04", "hello05", "hello06", "hello07", "hello08", "hello09", "hello10", "hello11", "hello12", "hello13"]
                mock_get.return_value.status_code = 404
                mock_get.return_value.json.return_value = {"name":"world",
                                                           "constants": [{"name": "foo", "value": "bar"}, {"name": "foo2", "value": "bar2"}]}
                retriever = connec.profiles()
                assert mock_get.call_args[0][0].startswith("/profiles/hello")
                assert len(retriever) == 0

    def return_mock_status(self, *args, **kwargs):
        errors = [1, 4, 6, 7, 12]
        status = 404 if self.test_profiles_with_5_error_step in errors else 200
        self.test_profiles_with_5_error_step += 1
        mock = Mock()
        type(mock).status_code = PropertyMock(return_value=status)
        mock.json.return_value = {"name": "world",
                                    "constants": [{"name": "foo", "value": "bar"}, {"name": "foo2", "value": "bar2"}]}
        return mock

    def test_profiles_with_5_not_found_error(self):
        self.test_profiles_with_5_error_step = 0
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.profiles_names") as mock_names:
            with patch("qarnot.connection.Connection._get") as mock_get:
                mock_names.return_value = ["hello01", "hello02", "hello03", "hello04", "hello05", "hello06", "hello07", "hello08", "hello09", "hello10", "hello11", "hello12", "hello13"]
                mock_get.side_effect = self.return_mock_status
                retriever = connec.profiles()
                assert mock_get.call_args[0][0].startswith("/profiles/hello")
                assert len(retriever) == 8

    def test_profile_details(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"name":"world",
                                               "constants": [{"name": "foo", "value": "bar"}, {"name": "foo2", "value": "bar2"}]}
            retriever = connec.profile_details("hello")
            assert retriever.name == "world" and retriever.constants == (('foo', 'bar'),('foo2', 'bar2'))
            assert "/profiles/hello" == mock_get.call_args[0][0]

    def test_paginate_task_retriever_url(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}
            retriever = connec.tasks_page(summary=False)
            assert "/tasks/paginate" == mock_page_call.call_args[0][0]
            retriever = connec.tasks_page(summary=True)
            assert "/tasks/summaries/paginate" == mock_page_call.call_args[0][0]

    def test_paginate_job_retriever_url(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}
            retriever = connec.jobs_page()
            assert "/jobs/paginate" == mock_page_call.call_args[0][0]

    def test_paginate_pool_retriever_url(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}
            retriever = connec.pools_page(summary=False)
            assert "/pools/paginate" == mock_page_call.call_args[0][0]
            retriever = connec.pools_page(summary=True)
            assert "/pools/summaries/paginate" == mock_page_call.call_args[0][0]

    @pytest.mark.parametrize("tags, tags_intersect, expected_filter", [
        (["tag1", "tag2"], None, expected_or_tags_filter),
        (None, ["tag_inter1", "tag_inter2"], expected_and_tags_filter),
        (["tag1", "tag2"], ["tag_inter1", "tag_inter2"], expected_and_tags_filter),
    ])
    def test_paginate_task_retriever_filter(self, tags, tags_intersect, expected_filter):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}

            retriever = connec.tasks_page(tags=tags, tags_intersect=tags_intersect)
            assert expected_filter == mock_page_call.call_args[0][1]["filter"]

    @pytest.mark.parametrize("tags, tags_intersect, expected_filter", [
        (["tag1", "tag2"], None, expected_or_tags_filter),
        (None, ["tag_inter1", "tag_inter2"], expected_and_tags_filter),
        (["tag1", "tag2"], ["tag_inter1", "tag_inter2"], expected_and_tags_filter),
    ])
    def test_paginate_job_retriever_filter(self, tags, tags_intersect, expected_filter):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}

            retriever = connec.jobs_page(tags=tags, tags_intersect=tags_intersect)
            assert expected_filter == mock_page_call.call_args[0][1]["filter"]

    @pytest.mark.parametrize("tags, tags_intersect, expected_filter", [
        (["tag1", "tag2"], None, expected_or_tags_filter),
        (None, ["tag_inter1", "tag_inter2"], expected_and_tags_filter),
        (["tag1", "tag2"], ["tag_inter1", "tag_inter2"], expected_and_tags_filter),
    ])
    def test_paginate_pool_retriever_filter(self, tags, tags_intersect, expected_filter):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}
            retriever = connec.pools_page(tags=tags, tags_intersect=tags_intersect)
            print(mock_page_call.call_args[0][1]["filter"])
            print(mock_page_call.call_args[0])
            print(mock_page_call.call_args)
            assert expected_filter == mock_page_call.call_args[0][1]["filter"]

    @pytest.mark.parametrize("token, max, expected_token, expected_max", [
        ("token", 1, "token", 1),
        (None, None, None, None),
    ])
    def test_paginate_task_retriever_paginate_page_values(self, token, max, expected_token, expected_max):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}

            retriever = connec.tasks_page(token=token, maximum=max)
            assert expected_token == mock_page_call.call_args[0][1]["token"]
            assert expected_max == mock_page_call.call_args[0][1]["maximumResults"]

    @pytest.mark.parametrize("token, max, expected_token, expected_max", [
        ("token", 1, "token", 1),
        (None, None, None, None),
    ])
    def test_paginate_job_retriever_paginate_request_values(self, token, max, expected_token, expected_max):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}

            retriever = connec.jobs_page(token=token, maximum=max)
            assert expected_token == mock_page_call.call_args[0][1]["token"]
            assert expected_max == mock_page_call.call_args[0][1]["maximumResults"]

    @pytest.mark.parametrize("token, max, expected_token, expected_max", [
        ("token", 1, "token", 1),
        (None, None, None, None),
    ])
    def test_paginate_pool_retriever_paginate_request_values(self, token, max, expected_token, expected_max):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":[]}
            retriever = connec.pools_page(token=token, maximum=max)
            assert expected_token == mock_page_call.call_args[0][1]["token"]
            assert expected_max == mock_page_call.call_args[0][1]["maximumResults"]

    def test_page_task_return_object(self):
        task_body = [{
            "uuid": "f78fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "name": "default_name",
            "profile": "docker-bash",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "creationDate": "2019-11-08T10:54:11Z",
            "state": "submetted",
        }, {
            "uuid": "078fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "name": "Second_default_name",
            "profile": "docker-bash2",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "creationDate": "2019-11-08T10:54:11Z",
            "state": "submetted",
        }]

        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":task_body}
            page_result = connec.tasks_page()
            assert page_result.token == "token"
            assert page_result.next_token == "nextToken"
            assert page_result.is_truncated == True
            result = page_result.page_data
            assert type(result[0]) == qarnot.task.Task
            assert result[0].uuid == "f78fdff8-7081-46e1-bb2f-d9cd4e185ece"
            assert result[1].uuid == "078fdff8-7081-46e1-bb2f-d9cd4e185ece"

    def test_page_job_return_object(self):
        job_body = [{
            "uuid": "f78fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "shortname": "f78fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "name": "default_name",
            "profile": "docker-bash",
            "instanceCount": 1,
            "poolUuid": None,
            "creationDate": "2019-11-08T10:54:11Z",
            "lastModified": "2019-11-08T10:54:11Z",
            "maxWallTime": "10:54:11",
            "state": "submetted",
            "useDependencies": False,
            "autoDeleteOnCompletion": False,
            "completionTimeToLive": None,
        }, {
            "uuid": "078fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "shortname": "078fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "name": "Second_default_name",
            "profile": "docker-bash2",
            "instanceCount": 1,
            "poolUuid": None,
            "creationDate": "2019-11-08T10:54:11Z",
            "lastModified": "2019-11-08T10:54:11Z",
            "maxWallTime": "10:54:11",
            "state": "submetted",
            "useDependencies": False,
            "autoDeleteOnCompletion": False,
            "completionTimeToLive": None,
        }]

        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token": "token", "nextToken": "nextToken", "isTruncated": True, "data": job_body}
            page_result = connec.jobs_page()
            assert page_result.token == "token"
            assert page_result.next_token == "nextToken"
            assert page_result.is_truncated == True
            result = page_result.page_data
            assert type(result[0]) == qarnot.job.Job
            assert result[0].uuid == "f78fdff8-7081-46e1-bb2f-d9cd4e185ece"
            assert result[1].uuid == "078fdff8-7081-46e1-bb2f-d9cd4e185ece"

    def test_page_pool_return_object(self):
        pool_body = [{
            "uuid": "f78fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "name": "default_name",
            "profile": "docker-bash",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "creationDate": "2019-11-08T10:54:11Z",
            "state": "submetted",
        }, {
            "uuid": "078fdff8-7081-46e1-bb2f-d9cd4e185ece",
            "name": "Second_default_name",
            "profile": "docker-bash2",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "creationDate": "2019-11-08T10:54:11Z",
            "state": "submetted",
        }]

        connec = self.get_connection()
        with patch("qarnot.connection.Connection._page_call") as mock_page_call:
            mock_page_call.return_value = {"token" : "token","nextToken" : "nextToken","isTruncated":True,"data":pool_body}
            page_result = connec.pools_page()
            assert page_result.token == "token"
            assert page_result.next_token == "nextToken"
            assert page_result.is_truncated == True
            result = page_result.page_data
            assert type(result[0]) == qarnot.pool.Pool
            assert result[0].uuid == "f78fdff8-7081-46e1-bb2f-d9cd4e185ece"
            assert result[1].uuid == "078fdff8-7081-46e1-bb2f-d9cd4e185ece"

    def test_page_request(self):
        connec = self.get_connection()
        assert {"filter": None, "token": None, "maximumResults": None} == connec._paginate_request(None, None, None)
        assert {"filter": {}, "token": "token", "maximumResults": 12} == connec._paginate_request({}, "token", 12)

    def test_offset_request(self):
        connec = self.get_connection()
        assert {"limit": None, "offset": None} == connec._offset_request(None, None)
        assert {"limit": 20, "offset": 1} == connec._offset_request(20, 1)

    def test_page_call_call_post(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._post") as mock_post:
            mock_post.return_value.json.return_value = {"token": "token", "nextToken": "nextToken", "isTruncated": True, "data": []}
            mock_post.return_value.status_code = 200
            connec._page_call("url", {})
            mock_post.assert_called_once_with("url", {})

    def test_page_call_raise_error_when_wrong_status_code(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._post") as mock_post:
            mock_post.return_value.status_code = 404
            mock_post.json.return_value = {"token": "token", "nextToken": "nextToken", "isTruncated": True, "data": []}
            with pytest.raises(qarnot.exceptions.QarnotGenericException):
                connec._page_call("url", {})

    def test_page_call_return_json(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._post") as mock_post:
            mock_post.return_value.status_code = 200
            json_ret = {"token": "token", "nextToken": "nextToken", "isTruncated": True, "data": []}
            mock_post.return_value.json.return_value = json_ret
            ret = connec._page_call("url", {})
            assert ret == json_ret

    def test_all_pages_break_when_false(self):
        connec = self.get_connection()
        mock1 = Mock()
        mock2 = Mock()
        mock3 = Mock()
        mock4 = Mock()
        mock5 = Mock()
        ret1 = Mock(next_token="next", is_truncated=True,page_data=[mock1, mock2])
        ret2 = Mock(next_token=None, is_truncated=False, page_data=[mock3, mock4])
        ret3 = Mock(next_token=None, is_truncated=False, page_data=[mock5])
        mock = Mock(side_effect=[ret1, ret2, ret3])
        ret = connec._all_pages(mock)
        assert mock1 in ret
        assert mock2 in ret
        assert mock3 in ret
        assert mock4 in ret
        assert mock5 not in ret

    def test_jobs(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.jobs_page") as mock_page_call:
            mock_page_call.return_value = qarnot.paginate.PaginateResponse("token", None, False, [])
            connec.jobs()
            mock_page_call.assert_called_once()

    def test_tasks(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.tasks_page") as mock_page_call:
            mock_page_call.return_value = qarnot.paginate.PaginateResponse("token", None, False, [])
            connec.tasks()
            mock_page_call.assert_called_once()

    def test_pools(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.pools_page") as mock_page_call:
            mock_page_call.return_value = qarnot.paginate.PaginateResponse("token", None, False, [])
            connec.pools()
            mock_page_call.assert_called_once()

    def test_all_jobs(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.jobs_page") as mock_page_call:
            mock_page_call.return_value = qarnot.paginate.PaginateResponse("token", None, False, [])
            iterator = connec.all_jobs()
            with pytest.raises(StopIteration):
                next(iterator)
            mock_page_call.assert_called_once()

    def test_all_tasks(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.tasks_page") as mock_page_call:
            mock_page_call.return_value = qarnot.paginate.PaginateResponse("token", None, False, [])
            iterator = connec.all_tasks()
            with pytest.raises(StopIteration):
                next(iterator)
            mock_page_call.assert_called_once()

    def test_all_pools(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.pools_page") as mock_page_call:
            mock_page_call.return_value = qarnot.paginate.PaginateResponse("token", None, False, [])
            iterator = connec.all_pools()
            with pytest.raises(StopIteration):
                next(iterator)
            mock_page_call.assert_called_once()

    def test_all_hardware_constraints(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection.hardware_constraints_page") as mock_page_call:
            mock_page_call.return_value = qarnot.paginate.OffsetResponse(2, 0, 50, []) # if total is less than the limit, call only one page is enough
            iterator = connec.all_hardware_constraints()
            with pytest.raises(StopIteration):
                next(iterator)
            mock_page_call.assert_called_once()
        with patch("qarnot.connection.Connection.hardware_constraints_page") as mock_page_call:
            mock_page_call.side_effect = [qarnot.paginate.OffsetResponse(100, 0, 50, []), qarnot.paginate.OffsetResponse(100, 51, 50, [])] # if total more than the limit, multiple pages need to be called
            iterator = connec.all_hardware_constraints()
            with pytest.raises(StopIteration):
                next(iterator)
            assert mock_page_call.call_count == 2

    def test_user_information(self):
        connec = self.get_connection()
        with patch("qarnot.connection.Connection._get") as get_user:
            user_json = {
                "email":"",
                "maxBucket":5,
                "bucketCount":6,
                "quotaBytesBucket":7,
                "usedQuotaBytesBucket":8,
                "taskCount":9,
                "maxTask":10,
                "runningTaskCount":11,
                "maxRunningTask":12,
                "maxInstances":13,
                "maxPool":14,
                "poolCount":15,
                "maxRunningPool":16,
                "runningPoolCount":17,
                "runningInstanceCount":18,
                "runningCoreCount":19,
            }
            get_user.return_value.status_code = 200
            get_user.return_value.json.return_value = user_json
            user = connec.user_info
            assert user.email == user_json.get('email', '')
            assert user.max_bucket == user_json['maxBucket']
            assert user.bucket_count == user_json.get('bucketCount', -1)
            assert user.quota_bytes_bucket == user_json['quotaBytesBucket']
            assert user.used_quota_bytes_bucket == user_json['usedQuotaBytesBucket']
            assert user.task_count == user_json['taskCount']
            assert user.max_task == user_json['maxTask']
            assert user.running_task_count == user_json['runningTaskCount']
            assert user.max_running_task == user_json['maxRunningTask']
            assert user.max_instances == user_json['maxInstances']
            assert user.max_pool == user_json['maxPool']
            assert user.pool_count == user_json['poolCount']
            assert user.max_running_pool == user_json['maxRunningPool']
            assert user.running_pool_count == user_json['runningPoolCount']
            assert user.running_instance_count == user_json['runningInstanceCount']
            assert user.running_core_count == user_json['runningCoreCount']

    def test_user_hardware_constraints(self):
        connect = self.get_connection()
        with patch("qarnot.connection.Connection._get") as get_hw_constraints:
            hw_constraints_page_json = {
                "data":[
                {
                    "discriminator": "MinimumCoreHardwareConstraint",
                    "coreCount": 16
                },
                {
                    "discriminator": "MaximumCoreHardwareConstraint",
                    "coreCount": 32
                },
                {
                    "discriminator": "MinimumRamCoreRatioHardwareConstraint",
                    "minimumMemoryGBCoreRatio": 0.4
                },
                {
                    "discriminator": "MaximumRamCoreRatioHardwareConstraint",
                    "maximumMemoryGBCoreRatio": 0.7
                },
                {
                    "discriminator": "SpecificHardwareConstraint",
                    "specificationKey": "R7-2700X"
                },
                {
                    "discriminator": "MinimumRamHardwareConstraint",
                    "minimumMemoryMB": 4000
                },
                {
                    "discriminator": "MaximumRamHardwareConstraint",
                    "maximumMemoryMB": 32000
                },
                {
                    "discriminator": "GpuHardwareConstraint"
                }],
                "offset": 0,
                "limit": 50,
                "total": 8
            }
            get_hw_constraints.return_value.status_code = 200
            get_hw_constraints.return_value.json.return_value = hw_constraints_page_json
            ret = connect.hardware_constraints_page()
            assert ret.total == hw_constraints_page_json['total']
            assert ret.page_data != None
            assert len(ret.page_data) == 8
