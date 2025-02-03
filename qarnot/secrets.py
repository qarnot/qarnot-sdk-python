"""Secrets prototype"""

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
# pylint: disable=W0613


from typing import Dict, List

from . import get_url, raise_on_error, raise_on_secrets_specific_error


class SecretAccessRightBySecret(object):
    """
        Secret to be made available to a task, described by exact match on its key property.
    """

    def __init__(self, key: str):
        """The SecretAccessRightBySecret constructor.

        :param key: the exact key of the secret.
        :type key: `str`
        """
        self._key = key

    def __str__(self) -> str:
        return "Secrets access by key \"{}\".".format(self._key)

    def __repr__(self) -> str:
        return self._key

    def __eq__(self, other) -> bool:
        if other is None or not isinstance(other, self.__class__):
            return False
        return self._key == other._key

    def to_json(self) -> Dict[str, str]:
        """Get a SecretAccessRightBySecret ready to be json packed.

        :return: the json representation of a secret accessible by exact match.
        :rtype: Dict[str,str]
        """
        return {"key": self._key}


class SecretAccessRightByPrefix(object):
    """
        Secrets to be made available to a task, by prefix match on its prefix property.
    """

    def __init__(self, prefix: str):
        """The SecretAccessRightByPrefix constructor.

        :param key: the prefix of the secrets' keys.
        :type key: `str`
        """
        self._prefix = prefix

    def __str__(self) -> str:
        return "Secrets access by prefix \"{}\".".format(self._prefix)

    def __repr__(self) -> str:
        return self._prefix

    def __eq__(self, other) -> bool:
        if other is None or not isinstance(other, self.__class__):
            return False
        return self._prefix == other._prefix

    def to_json(self) -> Dict[str, str]:
        """Get a SecretAccessRightByPrefix ready to be json packed.

        :return: the json representation of a secret accessible by prefix match.
        :rtype: Dict[str, str]
        """
        return {"prefix": self._prefix}


class SecretsAccessRights(object):
    """
        Description of all the secrets a task will have access to when running.
    """

    def __init__(self, by_secret: List[SecretAccessRightBySecret] = None, by_prefix: List[SecretAccessRightByPrefix] = None):
        """The SecretsAccessRights constructor

        :param by_secret: the list of secrets the task will have access to, described using an exact key match
        :type by_secret: `List[~qarnot.secrets.SecretAccessRightBySecret]`
        :param by_prefix: the list of secrets the task will have access to, described using a prefix key match
        :type by_prefix: `List[~qarnot.secrets.SecretAccessRightByPrefix]`
        """
        self._by_secret: List[SecretAccessRightBySecret] = by_secret or []
        self._by_prefix: List[SecretAccessRightByPrefix] = by_prefix or []

    def to_json(self) -> Dict[str, List[Dict[str, str]]]:
        """Get a SecretsAccessRights ready to be json packed.

        :return: the json representation of the secrets a task will have access to when running.
        :rtype: Dict[str, List[str]]
        """
        result: Dict[str, List[Dict[str, str]]] = {
            "bySecret": [by_secret.to_json() for by_secret in self._by_secret] or [],
            "byPrefix": [by_prefix.to_json() for by_prefix in self._by_prefix] or [],
        }

        return result

    @classmethod
    def from_json(cls, json: Dict[str, List[Dict[str, str]]]):
        """Create a SecretsAccessRights from a json representation

        :param json: the json to use to create the SecretsAccessRights object.
        :type json: `Dict[str, Any]`
        :returns: The created :class:`~qarnot.secrets.SecretsAccessRights`.
        """
        by_secret, by_prefix = None, None
        if "bySecret" in json:
            by_secret = [SecretAccessRightBySecret(secret.get("key")) for secret in json.get("bySecret")]
        if "byPrefix" in json:
            by_prefix = [SecretAccessRightByPrefix(secret.get("prefix")) for secret in json.get("byPrefix")]

        return SecretsAccessRights(by_secret=by_secret, by_prefix=by_prefix)

    def add_secret_by_key(self, key: str):
        """Add `key` as an available secret to the task.

        :param key: Key to exactly match secrets on.
        :type key: `str`
        """
        self._by_secret.append(SecretAccessRightBySecret(key))
        return self

    def add_secrets_by_keys(self, keys: List[str]):
        """Add multiple keys as available secrets to the task.

        :param key: Keys to exactly match secrets on.
        :type key: `List[str]`
        """
        self._by_secret.extend(SecretAccessRightBySecret(key) for key in keys)
        return self

    def add_secret_by_prefix(self, prefix: str):
        """Add all secrets starting with `prefix` as available secrets to the task.

        :param prefix: Prefix to match secrets against.
        :type prefix: `str`
        """
        self._by_prefix.append(SecretAccessRightByPrefix(prefix))
        return self

    def add_secrets_by_prefixes(self, prefixes: List[str]):
        """Add all secrets starting with any of the `prefixes` as available secrets to the task.

        :param prefixes: Prefixes to match secrets against.
        :type prefixes: `List[str]`
        """
        self._by_prefix.extend(SecretAccessRightByPrefix(prefix) for prefix in prefixes)
        return self

    def __bool__(self):
        return abs(len(self._by_secret)) + abs(len(self._by_prefix)) > 0


class Secrets(object):
    """
        Client used to interact with the Qarnot secrets API.
    """

    def __init__(self, connection):
        """The Secrets constructor.

        :param connection: the cluster one where secrets are retrieved.
        :type connection: `qarnot.connection.Connection`
        """
        self._connection = connection

    def _get_secret_raw(self, key: str):
        """Retrieves the value of the secret with key `key`.

        :param key: the key of the secret
        :type key: `str`
        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.SecretNotFoundException: Secret was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        key = key.strip('/')
        response = self._connection._get(get_url('secrets data', secret_key=key))
        raise_on_secrets_specific_error(response)
        raise_on_error(response)
        return response

    def get_secret(self, key: str) -> str:
        """Retrieves the value of the secret with key `key` and parses it to a string.

        :param key: the key of the secret
        :type key: `str`
        :rtype: str
        :raises ~qarnot.exceptions.SecretNotFoundException: Secret was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        raw_secret = self._get_secret_raw(key)
        return raw_secret.json().get("value")

    def _create_secret_raw(self, key: str, value: str):
        """Creates a secret with key `key` and value `value`.

        :param key: the key of the secret
        :type key: `str`
        :param value: the value of the secret
        :type value: `str`
        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.SecretConflictException: Secret with this key already exists.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        key = key.strip('/')
        response = self._connection._put(get_url('secrets data', secret_key=key), json={"Value": value})
        raise_on_secrets_specific_error(response)
        raise_on_error(response)
        return response

    def create_secret(self, key: str, value: str) -> str:
        """Creates a secret with key `key` and value `value`. Returns back the key.

        :param key: the key of the secret
        :type key: `str`
        :param value: the value of the secret
        :type value: `str`
        :rtype: `str`
        :raises ~qarnot.exceptions.SecretConflictException: Secret with this key already exists.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        key = key.strip('/')
        _ = self._create_secret_raw(key, value)
        return key

    def update_secret(self, key: str, value: str) -> None:
        """Updates secret with key `key` and sets its value to `value`.

        :param key: the key of the secret
        :type key: `str`
        :param value: the new value of the secret
        :type value: `str`
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.SecretNotFoundException: The secret was not found.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        key = key.strip('/')
        response = self._connection._patch(get_url('secrets data', secret_key=key), json={"Value": value})
        raise_on_secrets_specific_error(response)
        raise_on_error(response)

    def delete_secret(self, key: str) -> None:
        """Deletes secret with key `key`.

        :param key: the key of the secret
        :type key: `str`
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.SecretNotFoundException: The secret was not found.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        key = key.strip('/')
        response = self._connection._delete(get_url('secrets data', secret_key=key))
        raise_on_secrets_specific_error(response)
        raise_on_error(response)

    def list_secrets(self, prefix: str, recursive: bool = False) -> List[str]:
        """Lists all the secrets starting with `prefix`

        When not using recursive mode, only keys and folders directly under `prefix` are
        returned. For example, listing with a prefix of "prefix" will return "prefix/a" but
        won't return "prefix/a/b". Folders can be identified by a trailing "/", for example
        "prefix/nested/".
        When in recursive mode, only the secrets are returned, not the folders.

        :param prefix: the prefix
        :type prefix: `str`
        :param recursive: lists secrets recursively or not (defaults to `False`)
        :type recursive: `bool`
        :rtype: `List[str]`
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        if not recursive:
            return self._list_secrets_once(prefix)

        results: List[str] = []
        pending: List[str] = [prefix]

        while pending:
            key = pending.pop()
            keys = self._list_secrets_once(key)
            results.extend(k for k in keys if not k.endswith('/'))
            pending.extend(k for k in keys if k.endswith('/'))

        return results

    def _list_secrets_once(self, prefix: str) -> List[str]:
        prefix = prefix.strip('/')
        response = self._connection._get(get_url('secrets search', secret_prefix=prefix))
        raise_on_secrets_specific_error(response)
        raise_on_error(response)
        return ["{}/{}".format(prefix, key) if prefix else key for key in response.json().get("keys")]
