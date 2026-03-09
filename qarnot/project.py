"""Module to handle a project."""

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


class Project(object):
    """Represents an organization project.

    .. note::
       A :class:`Project` must be retrieved with :attr:`qarnot.connection.Connection.user_info.projects`.
    """
    def __init__(self, uuid: str):
        """Create a new :class:`Project`.

        :param uuid: identifier of the project
        :type uuid: :class:`str`
        """
        self._name: str = None
        self._uuid: str = uuid
        self._slug: str = None
        self._organization_uuid: str = None
        self._description: str = None
        self._is_default: bool = None

    @property
    def uuid(self):
        """:type: :class:`str`
        :getter: Returns this project's uuid

        The project's uuid.

        Automatically set when a project is submitted.
        """
        return self._uuid

    @property
    def name(self):
        """:type: :class:`str`
        :getter: Returns this project's name

        The project's name.
        """
        return self._name

    @property
    def slug(self):
        """:type: :class:`str`
        :getter: Returns this project's slug name

        The project's slug name.

        The project's slug is be DNS compliant and unique. It can be used to identified a project instead of its uuid.
        """
        return self._slug

    @property
    def description(self):
        """:type: :class:`str`
        :getter: Returns this project's description

        The project's description.
        """
        return self._description

    @property
    def organization_uuid(self):
        """:type: :class:`str`
        :getter: Returns this project's organization's uuid

        The uuid of the organization this project is attached to.
        """
        return self._organization_uuid

    @property
    def is_default(self):
        """:type: :class:`bool`
        :getter: Returns true if this project is the default one of the organization

        The project's description.
        """
        return self._is_default

    @staticmethod
    def retrieve_by_uuid(connection, uuid):
        """Retrieve project given its uuid.

        :param qarnot.connection.Connection connection:
          the cluster to retrieve the project from
        :param str uuid: the uuid of the project to retrieve

        :rtype: Project
        :returns: The retrieved project.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingProjectException: no such project
        """
        return next((proj for proj in connection.user_info.projects if proj.uuid == uuid), None)

    @staticmethod
    def retrieve_by_slug(connection, slug):
        """Retrieve project given its slug.

        :param qarnot.connection.Connection connection:
          the cluster to retrieve the project from
        :param str slug: the slug of the project to retrieve

        :rtype: Project
        :returns: The retrieved project.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingProjectException: no such project
        """
        return next((proj for proj in connection.user_info.projects if proj.slug == slug), None)

    @staticmethod
    def retrieve_by_name(connection, name):
        """Retrieve project given its name.

        :param qarnot.connection.Connection connection:
          the cluster to retrieve the project from
        :param str name: the name of the project to retrieve

        :rtype: Project
        :returns: The retrieved project.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingProjectException: no such project
        """
        return next((proj for proj in connection.user_info.projects if proj.name == name), None)

    @classmethod
    def from_json(cls, payload):
        """Create a Project object from a json project.

        :param qarnot.connection.Connection connection: the cluster connection
        :param dict json_project: Dictionary representing the project
        :returns: The created :class:`~qarnot.project.project`.
        """
        project = cls(payload.get("uuid"))

        project._uuid = payload.get("uuid")
        project._name = payload.get("name")
        project._slug = payload.get("slug")
        project._description = payload.get("description")
        project._organization_uuid = payload.get("organizationUuid")
        project._is_default = payload.get("isDefault")
        if project._is_default is None and project._slug is not None:
            project._is_default = project._slug == "default"

        return project

    def __repr__(self):
        return 'Project {0} - {1} - {2} from Organization: {3} (isDefault: {4}) : {5}'\
            .format(self._name,
                    self._slug,
                    self._uuid,
                    self._organization_uuid,
                    self._is_default,
                    self._description)
