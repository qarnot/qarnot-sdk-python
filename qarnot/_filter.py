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

def all_tag_filter(tags):
    """Return a filter of the element by all the tags for a json post advance search.
    :param List of :class:`str` tags: Desired filtering tags

    :returns: json structure to call the the asking tasks.
    """

    if not isinstance(tags, list):
        tags = [tags]
    tag_selector = {
        "Filter":
        {
            "Operator": "And",
            "Filters":
            [
                {
                    "Operator": "Equal",
                    "Field": "Tags",
                    "Value": tag_value
                } for tag_value in tags
            ]
        }
    }
    return tag_selector
