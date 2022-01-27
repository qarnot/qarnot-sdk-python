from typing import Any, Dict
import abc
from . import _util

# ********************************************************
# *******************  Filtering  ************************
# ********************************************************


class AbstractFiltering(metaclass=abc.ABCMeta):
    """
    Abstract base class for resources filtering, allowing to select only a subset of a resources bucket as task resources.
    """

    name: str = 'abstractFiltering'

    @abc.abstractmethod
    def to_json(self):
        """Get a dict ready to be json packed.

        :raises NotImplementedError: this is an abstract method, it should be overridden in child classes
        """

    @classmethod
    @abc.abstractmethod
    def from_json(cls, json):
        """Static method called to create the class obj from a json object.

        :param json: the json elements of the class
        :type json: Dict
        :raises NotImplementedError: this is an abstaract method, override it in it's child classes.
        """

    @abc.abstractmethod
    def sanitize_filter_paths(self):
        """Sanitize the filters bucket path by removing extra separators

        :raises NotImplementedError: this is an abstract method, it should be overridden in child classes
        """


class BucketPrefixFiltering(AbstractFiltering):
    """
        Allows to filter a resources bucket by name prefix. Only bucket files starting with the given prefix will be used as task resources.
    """
    name: str = 'prefixFiltering'

    def __init__(self, prefix: str):
        self.prefix = prefix

    @classmethod
    def from_json(cls, json: Dict[str, str]):
        """Static method called to create the class obj from a json object.

        :param json: the json elements of the class
        :type json: `dict`
        "bucket_or_bucket_name""
        """
        prefix: str = json.get("prefix")
        return BucketPrefixFiltering(prefix)

    def __repr__(self) -> str:
        return "Filtering: {}  prefix: {}".format(self.name, self.prefix)

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "prefix": self.prefix
        }

    def sanitize_filter_paths(self, show_warnings: bool):
        """ Sanitize bucket prefix path"""
        self.prefix = _util.get_sanitized_bucket_path(self.prefix, show_warnings)


class Filtering(object):
    """
        Groups the various object filters on an advanced resources bucket.
    """

    def __init__(self):
        self._filters = {}

    def __repr__(self) -> str:
        return "[" + ",".join(map(str, self._filters.values())) + "]"

    def append(self, filtering: AbstractFiltering):
        """Add a new filtering object

        :param filtering: a filtering object of the bucket
        :type filtering: `AbstractFiltering`
        """
        self._filters[filtering.name] = filtering

    @classmethod
    def from_json(cls, json) -> 'Filtering':
        """Create the class sub objects of a Filtering from a json.

        :param json: the json elements of the class
        :type json: `dict`
        """
        filtering = Filtering()
        for key in json:
            if BucketPrefixFiltering.name == key:
                filtering.append(BucketPrefixFiltering.from_json(json[key]))
        return filtering

    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.
        """
        json = {}
        for key in self._filters:
            json[key] = self._filters[key].to_json()
        return json

    def sanitize_filter_paths(self, show_warning: bool):
        for resource_name in self._filters:
            self._filters[resource_name].sanitize_filter_paths(show_warning)

# ********************************************************
# *************  ResourcesTransformation  ****************
# ********************************************************


class AbstractResourcesTransformation(metaclass=abc.ABCMeta):
    """
    Abstract base class for resources transformation, allowing to transform bucket objects before they are presented to the task as resources.
    """
    name: str = 'abstractResourcesTransformation'

    @abc.abstractmethod
    def to_json(self):
        """Get a dict ready to be json packed.
        """

    @classmethod
    @abc.abstractmethod
    def from_json(cls, json):
        """Static method called to create the class obj from a json object.

        :param json: the json elements of the class
        :type json: `dict`
        """

    @abc.abstractmethod
    def sanitize_transformation_paths(self):
        """Sanitize the bucket path by removing extra separators

        :raises NotImplementedError: this is an abstract method, it should be overridden in child classes
        """


class PrefixResourcesTransformation(AbstractResourcesTransformation):
    """
        Allows to remove a prefix from bucket files before they are presented to the task. During execution, the task will see files with paths stripped of the given prefix in its working directory.
    """
    name: str = 'stripPrefix'

    def __init__(self, prefix: str):
        """The PrefixResourcesTransformation constructor

        :param prefix: the prefix path of the resource bucket to be removed.
        :type prefix: `str`
        """
        self.prefix = prefix

    def __repr__(self) -> str:
        return "ResourcesTransformation: {}  prefix: {}".format(self.name, self.prefix)

    @classmethod
    def from_json(cls, json):
        """Create a new instance of the class using the given json object.

        :param json: The Json object representation.
        :type json: `dict`
        :return: The PrefixResourcesTransformation new object
        :rtype: :class:`PrefixResourcesTransformation`
        """
        return PrefixResourcesTransformation(json["prefix"])

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        """
        return {
            "prefix": self.prefix
        }

    def sanitize_transformation_paths(self, show_warnings: bool):
        """ Sanitize bucket strip prefix path"""
        self.prefix = _util.get_sanitized_bucket_path(self.prefix, show_warnings)


class ResourcesTransformation(object):
    """
        Groups the various object transformation on an advanced resources bucket.
    """
    def __init__(self):
        self._resource_transformers = {}

    def append(self, resource: AbstractResourcesTransformation):
        """Add a new resource transformation object

        :param filtering: a filtering object of the bucket
        :type filtering: `AbstractResourcesTransformation`
        """
        self._resource_transformers[resource.name] = resource

    def __repr__(self) -> str:
        return "[" + ",".join(map(str, self._resource_transformers.values())) + "]"

    @classmethod
    def from_json(cls, json) -> 'ResourcesTransformation':
        """Create the class sub objects of a ResourcesTransformation from a json.

        :param json: the json elements of the class
        :type json: `dict`
        """
        resource = ResourcesTransformation()
        for key in json.keys():
            if PrefixResourcesTransformation.name == key:
                resource.append(
                    PrefixResourcesTransformation.from_json(json[key]))
        return resource

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        """
        json = {}
        for key in self._resource_transformers.keys():
            json[key] = self._resource_transformers[key].to_json()
        return json

    def sanitize_transformation_paths(self, show_warning: bool):
        for resource_name in self._resource_transformers:
            self._resource_transformers[resource_name].sanitize_transformation_paths(show_warning)
