import pytest
# import mock
import qarnot
from qarnot.pool import Pool
from qarnot.task import Task
from qarnot.bucket import Bucket
from qarnot.advanced_bucket import AbstractFiltering, BucketPrefixFiltering, Filtering, PrefixResourcesTransformation, ResourcesTransformation
import datetime
from .mock_connection import MockConnection

class TestAdvancedResourceBucketsMethods:
    def test_check_the_init_values(self):
        bucket = Bucket(MockConnection(), "name", False)
        bucket2 = bucket.with_filtering(BucketPrefixFiltering("test")).with_resource_transformation(PrefixResourcesTransformation("test2"))
        assert "name" == bucket2.uuid
        assert "test" == bucket2._filtering._filters["prefixFiltering"].prefix
        assert "test2" == bucket2._resources_transformation._resource_transformers["stripPrefix"].prefix
        bucket = Bucket(MockConnection(), "name", False)
        bucket2 = bucket.with_resource_transformation(PrefixResourcesTransformation("test2")).with_filtering(BucketPrefixFiltering("test"))
        assert "name" == bucket2.uuid
        assert "test" == bucket2._filtering._filters["prefixFiltering"].prefix
        assert "test2" == bucket2._resources_transformation._resource_transformers["stripPrefix"].prefix

    def test_create_an_advance_resource_json(self):
        """
        {
            BucketName:"name",
            Filtering: {
                BucketPrefixFiltering: {
                    Prefix:"prefix"
                }
            },
            ResourcesTransformation: {
                StripPrefix: {
                    Prefix:"prefix"
                }
            }
        }
        """
        bucket = Bucket(MockConnection(), "name", False)
        bucket2 = bucket.with_filtering(BucketPrefixFiltering("prefix1")).with_resource_transformation(PrefixResourcesTransformation("prefix2"))
        json_dict = bucket2.to_json()
        assert "name" == json_dict["bucketName"]
        assert "prefix1" == json_dict["filtering"]["prefixFiltering"]["prefix"]
        assert "prefix2" == json_dict["resourcesTransformation"]["stripPrefix"]["prefix"]

    def test_create_an_advance_bucket_from_a_json(self):
        json = {
            "bucketName": "name",
            "filtering": {
                "prefixFiltering": {
                    "prefix": "prefix1"
                }
            },
            "resourcesTransformation": {
                "stripPrefix": {
                    "prefix": "prefix2"
                }
            }
        }

        bucket = Bucket.from_json(MockConnection(), json)
        assert "name" == bucket.uuid
        assert "prefix1" == bucket._filtering._filters["prefixFiltering"].prefix
        assert "prefix2" == bucket._resources_transformation._resource_transformers["stripPrefix"].prefix

    def test_sanitize_advanced_bucket(self):
        filtering = Filtering()
        filtering.append(BucketPrefixFiltering("/some//Invalid///Path/"))
        filtering.sanitize_filter_paths(True)
        assert "some/Invalid/Path/" == filtering._filters[BucketPrefixFiltering.name].prefix
        filtering = Filtering()
        filtering.append(BucketPrefixFiltering("\\some\\\\Invalid\\\\\\Path\\"))
        filtering.sanitize_filter_paths(True)
        assert "some\\Invalid\\Path\\" == filtering._filters[BucketPrefixFiltering.name].prefix

        transformation = ResourcesTransformation()
        transformation.append(PrefixResourcesTransformation("/some//Invalid///Path/"))
        transformation.sanitize_transformation_paths(True)
        assert "some/Invalid/Path/" == transformation._resource_transformers[PrefixResourcesTransformation.name].prefix
        transformation = ResourcesTransformation()
        transformation.append(PrefixResourcesTransformation("\\some\\\\Invalid\\\\\\Path\\"))
        transformation.sanitize_transformation_paths(True)
        assert "some\\Invalid\\Path\\" == transformation._resource_transformers[PrefixResourcesTransformation.name].prefix
