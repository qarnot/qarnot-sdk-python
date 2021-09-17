import pytest
import qarnot
from qarnot.job import Job
from qarnot.pool import Pool
import datetime
from .mock_job import default_json_job
from .mock_connection import MockConnection

class TestJobProperties:
    conn = MockConnection()
    def submit_job(self, job):
        job._uuid = "submitted"

    def test_max_wall_time_accept_delta_before_submit(self):
        job = Job(self.conn, "job-name")
        delta = datetime.timedelta(days=2, hours=33, minutes=66, seconds=66)
        job.max_wall_time = delta
        assert "3.10:07:06" == job.max_wall_time

    def test_max_wall_time_accept_string_before_submit(self):
        job = Job(self.conn, "job-name")
        job.max_wall_time = "3.10:07:04"
        assert "3.10:07:04" == job.max_wall_time

    def test_max_wall_time_throw_exception_delta_after_submit(self):
        job = Job(self.conn, "job-name")
        self.submit_job(job)
        delta = datetime.timedelta(days=2, hours=33, minutes=66, seconds=66)
        with pytest.raises(AttributeError):
            job.max_wall_time = delta
        with pytest.raises(AttributeError):
            job.max_wall_time = "3.10:07:04"

    def test_max_wall_time_setting_throw_exception_with_number(self):
        job = Job(self.conn, "job-name")
        with pytest.raises(TypeError):
            job.max_wall_time = 10

    def test_name_is_set_before_submit(self):
        job = Job(self.conn, "job-name")
        job.name = "name"
        assert "name" == job.name

    def test_name_setting_throw_exception_after_submitted(self):
        job = Job(self.conn, "job-name")
        self.submit_job(job)
        with pytest.raises(AttributeError):
            job.name = "name"

    def test_shortname_is_set_before_submit(self):
        job = Job(self.conn, "job-name")
        job.shortname = "shortname"
        assert "shortname" == job.shortname

    def test_shortname_setting_throw_exception_after_submitted(self):
        job = Job(self.conn, "job-name")
        self.submit_job(job)
        with pytest.raises(AttributeError):
            job.shortname = "shortname"

    def test_use_dependencies_is_set_before_submit(self):
        job = Job(self.conn, "job-name")
        job.use_dependencies = True
        assert True == job.use_dependencies

    def test_use_dependencies_setting_throw_exception_after_submitted(self):
        job = Job(self.conn, "job-name")
        self.submit_job(job)
        with pytest.raises(AttributeError):
            job.use_dependencies = True

    def test_pool_is_set_before_submit(self):
        job = Job(self.conn, "job-name")
        pool = Pool(self.conn, "pool-name", "profile", 2, "shortname")
        job.pool = pool
        assert pool.shortname == job.pool.shortname

    def test_pool_setting_throw_exception_after_submitted(self):
        job = Job(self.conn, "job-name")
        self.submit_job(job)
        pool = Pool(self.conn, "pool-name", "profile", 2, "shortname")
        with pytest.raises(AttributeError):
            job.pool = pool

    def test_job_autodelete_default_value(self):
        job = Job(self.conn, "job-name")
        assert False == job.auto_delete

    def test_job_completion_ttl_default_value(self):
        job = Job(self.conn, "job-name")
        assert "00:00:00" == job.completion_ttl

    def test_job_autodelete_set_get(self):
        job = Job(self.conn, "job-name")
        job.auto_delete = False
        assert False == job.auto_delete
        job.auto_delete = True
        assert True == job.auto_delete

    def test_job_completion_ttl_set_get(self):
        job = Job(self.conn, "job-name")
        job.completion_ttl = datetime.timedelta(days=2, hours=33, minutes=66, seconds=66)
        assert "3.10:07:06" == job.completion_ttl
        job.completion_ttl = "4.11:08:06"
        assert "4.11:08:06" == job.completion_ttl

    def test_job_are_in_job_to_json(self):
        job = Job(self.conn, "job-name")
        job.completion_ttl = "4.11:08:06"
        job.auto_delete = True
        json_job = job._to_json()

        assert json_job['completionTimeToLive'] == '4.11:08:06'
        assert json_job['autoDeleteOnCompletion'] == True

    @pytest.mark.parametrize("property_name, expected_value", [
        ("previous_state", None),
        ("state_transition_time", None),
        ("previous_state_transition_time", None),
    ])
    def test_job_property_default_value(self, property_name,  expected_value):
        job = Job(self.conn, "job-name")
        assert getattr(job, property_name) is expected_value

    @pytest.mark.parametrize("property_name, set_value, expected_value", [
        ("max_wall_time", datetime.timedelta(days=2, hours=33, minutes=66, seconds=66), "3.10:07:06")
    ])
    def test_job_set_property_value(self, property_name, set_value, expected_value):
        job = Job(self.conn, "job-name")
        setattr(job, property_name, set_value)
        assert getattr(job, property_name) == expected_value

    @pytest.mark.parametrize("property_name, set_value, exception", [
        ("max_wall_time", 10, TypeError)
    ])
    def test_job_set_forbidden_property_raise_exception(self, property_name, set_value, exception):
        job = Job(self.conn, "job-name")
        with pytest.raises(exception):
            setattr(job, property_name, set_value)

    @pytest.mark.parametrize("property_name, set_value, exception", [
        ("max_wall_time", datetime.timedelta(seconds=66), AttributeError),
        ("name", "test", AttributeError),
    ])
    def test_job_set_property_raise_exception_after_submitted(self, property_name, set_value, exception):
        job = Job(self.conn, "job-name")
        self.submit_job(job)
        with pytest.raises(exception):
            setattr(job, property_name, set_value)

    @pytest.mark.parametrize("property_name, expected_value", [
        ("previous_state", default_json_job["previousState"]),
        ("state_transition_time", default_json_job["stateTransitionTime"]),
        ("previous_state_transition_time", default_json_job["previousStateTransitionTime"]),
    ])
    def test_job_property_update_value(self, property_name, expected_value):
        job = Job(self.conn, "job-name")
        job._update(default_json_job)
        assert getattr(job, property_name) is expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("name", default_json_job["name"]),
    ])
    def test_job_property_send_to_json_representation(self, property_name, expected_value):
        job = Job(self.conn, "job-name")
        job._update(default_json_job)
        job_json = job._to_json()
        assert job_json[property_name] is expected_value
