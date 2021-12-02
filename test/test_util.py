from qarnot._util import get_sanitized_bucket_path

class TestUtilTools:

    def test_sanitize_bucket_path(self):
        assert "some/Invalid/Path/" == get_sanitized_bucket_path("/some//Invalid///Path/")
        assert "some\\Invalid\\Path\\" == get_sanitized_bucket_path("\\some\\\\Invalid\\\\\\Path\\")
