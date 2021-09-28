# Copyright 2017 Qarnot computing
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, List, Dict, Optional, NewType


ApiFilter = NewType('ApiFilter', Dict[str, Any])
ApiFilterLeaf = ApiFilter
ApiFilterNode = ApiFilter


class Filters:
    """The qarnot advance filtering methods
    """
    @staticmethod
    def data_detail(filters: ApiFilter = None, select: List[str] = None, maximum_results: Optional[int] = None) -> Dict[str, Any]:
        """The qarnot data detail filter,
        it allow to filter the task, pools and jobs and select the fields to be retrieve.
        It is not compatible with the pagination.

        :param filters: the filtering option, defaults to None
        :type filters: Dict, optional
        :param select: a list of fields to retrieve, defaults to None
        :type select: List[str], optional
        :param maximum_results: [description], defaults to None
        :type maximum_results: int, optional
        :return: The data detail objet
        :rtype: Dict
        """
        return {
            "filter": filters,
            "select": select,
            "maximumResults": maximum_results,
        }

    @staticmethod
    def node_or(filters: List[ApiFilter]) -> ApiFilterNode:
        """Filter for checking an OR filter list
        For more information see the API documentation

        :param filters: the filter list to be concat
        :type filters: List
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilter({"operator": "Or", "filters": filters})

    @staticmethod
    def node_and(filters: List[ApiFilter]) -> ApiFilterNode:
        """Filter for checking an AND filter list
        For more information see the API documentation

        :param filters: the filter list to be concat
        :type filters: List
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilter({"operator": "And", "filters": filters})

    @staticmethod
    def equal(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with the field value equal to `value`
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the value to check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "Equal",
            "field": field,
            "value": value
        })

    @staticmethod
    def not_equal(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with field value different from `value`
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the value to check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "NotEqual",
            "field": field,
            "value": value
        })

    @staticmethod
    def inside(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with `value` inside the field value
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the values to be check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "In",
            "field": field,
            "value": value
        })

    @staticmethod
    def not_inside(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with `value` not inside the field value
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the values to be check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "NotIn",
            "field": field,
            "value": value
        })

    @staticmethod
    def less_or_equal(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with the field value lower or equal to `value`
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the value to check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "LessThanOrEqual",
            "field": field,
            "value": value
        })

    @staticmethod
    def less(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with the field value lower to `value`
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the value to check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "LessThan",
            "field": field,
            "value": value
        })

    @staticmethod
    def greater_or_equal(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with the field value greater or equal to `value`
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the value to check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "GreaterThanOrEqual",
            "field": field,
            "value": value
        })

    @staticmethod
    def greater(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with the field value greater to `value`
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the value to check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "GreaterThan",
            "field": field,
            "value": value
        })

    @staticmethod
    def like(field: str, value: Any) -> ApiFilterLeaf:
        """Filter to get objects with the field value matching the regex `value`
        For more information see the API documentation

        :param str field: the field to be check
        :param str value: the regex value to check
        :return: A Json filter formated
        :rtype: Dict
        """
        return ApiFilterLeaf({
            "operator": "Like",
            "field": field,
            "value": value
        })


def concat_filters(filters, exclude_filter=True):
    """Check and concat a list of API filters.

    :param filters: the filter list to be concat
    :type filters: List
    :param exclude_filter: Do an AND concat or a OR
    :type exclude_filter: Bool
    :return: A Json filter formated or None if there is no filters
    :rtype: Dict
    """
    if len(filters) == 0:
        return None
    if len(filters) == 1:
        return filters[0]
    return Filters.node_and(filters) if (exclude_filter) else Filters.node_or(filters)


def all_tag_filter(tags):
    """Return a filter of the element by all the tags for a json post advance search.
    :param List of :class:`str` tags: Desired filtering tags

    :returns: json structure to call the asking tasks.
    """

    if not isinstance(tags, list):
        tags = [tags]
    if len(tags) == 1:
        return Filters.equal("Tags", tags[0])
    tag_selector = Filters.node_and([Filters.equal("Tags", tag_value) for tag_value in tags])
    return tag_selector


def or_tag_filter(tags):
    """Return a "filter by any tags" of the element to create a json advance search.
    :param List of :class:`str` tags: Desired filtering tags

    :returns: json structure to call the asking tasks.
    """

    if not isinstance(tags, list):
        tags = [tags]
    if len(tags) == 1:
        return Filters.equal("Tags", tags[0])
    tag_selector = {
        "operator": "Or",
        "filters":
        [Filters.equal("Tags", tag_value) for tag_value in tags]
    }
    return tag_selector


def create_pool_filter(tags, tags_intersect):
    """Create a new advance search pool filter depending of the pool values.
    :param List of :class:`str` tags: Desired filtering tags
    :param List of :class:`str` tags: Desired filtering tags_intersect

    :returns: the advance search json filter.
    """

    filters = []
    if tags_intersect:
        filters.append(all_tag_filter(tags_intersect))
    elif tags:
        filters.append(or_tag_filter(tags))
    return concat_filters(filters)


def create_task_filter(tags, tags_intersect):
    """Create a new advance search task filter depending of the task values.
    :param List of :class:`str` tags: Desired filtering tags
    :param List of :class:`str` tags: Desired filtering tags_intersect

    :returns: the advance search json filter.
    """
    filters = []
    if tags_intersect:
        filters.append(all_tag_filter(tags_intersect))
    elif tags:
        filters.append(or_tag_filter(tags))
    return concat_filters(filters)


def create_job_filter(tags, tags_intersect):
    """Create a new advance search job filter depending of the job values.
    :param List of :class:`str` tags: Desired filtering tags
    :param List of :class:`str` tags: Desired filtering tags_intersect

    :returns: the advance search json filter.
    """
    filters = []
    if tags_intersect:
        filters.append(all_tag_filter(tags_intersect))
    elif tags:
        filters.append(or_tag_filter(tags))
    return concat_filters(filters)
