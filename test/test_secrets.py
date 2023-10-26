import pytest
import qarnot
from qarnot.secrets import SecretAccessRightBySecret, SecretAccessRightByPrefix, Secrets, SecretsAccessRights
from test.mock_connection import MockConnection, MockResponse


class TestSecretsAccessRights:

    @pytest.mark.parametrize("secrets_by_key, secrets_by_prefix", [
        ( [SecretAccessRightBySecret("keyOne"), SecretAccessRightBySecret("key/two")] , [] ),
        ( [], [SecretAccessRightByPrefix("prefixOne"), SecretAccessRightByPrefix("prefix/two")]),
        ( [SecretAccessRightBySecret("keyOne"), SecretAccessRightBySecret("key/two")] , [SecretAccessRightByPrefix("prefixOne"), SecretAccessRightByPrefix("prefix/two")])
    ])
    def test_to_json(self, secrets_by_key, secrets_by_prefix):
        secrets = SecretsAccessRights(secrets_by_key, secrets_by_prefix)
        json = secrets.to_json()

        assert "bySecret" in json
        assert "byPrefix" in json

        print(json)

        assert len(json["bySecret"]) == len(secrets_by_key)
        assert len(json["byPrefix"]) == len(secrets_by_prefix)

        assert all({"key" : value._key} for value in secrets_by_key)
        assert all({"prefix" : value._prefix} for value in secrets_by_prefix)

    @pytest.mark.parametrize("json", [
        {
            "bySecret": [
                {"key": "keyOne"},
                {"key": "another/key"},
            ],
            "byPrefix": []
        } ,
        {
            "bySecret": [],
            "byPrefix": [
                {"prefix": "prefixOne"},
                {"prefix": "another/prefix"},
            ]
        },
        {
            "bySecret": [
                {"key": "keyOne"},
                {"key": "another/key"},
            ],
            "byPrefix": [
                {"prefix": "prefixOne"},
                {"prefix": "another/prefix"},
            ]
        }
    ])
    def test_from_json(self, json):
        by_secrets = [ SecretAccessRightBySecret(value["key"]) for value in json["bySecret"]]
        by_prefix = [ SecretAccessRightByPrefix(value["prefix"]) for value in json["byPrefix"]]
        secrets = SecretsAccessRights.from_json(json)

        assert len(secrets._by_secret) == len(by_secrets)
        assert len(secrets._by_prefix) == len(by_prefix)

        assert all( secret in secrets._by_secret for secret in by_secrets )
        assert all( secret in secrets._by_prefix for secret in by_prefix )

        assert SecretAccessRightBySecret("junk key") not in secrets._by_secret
        assert SecretAccessRightByPrefix("junk prefix") not in secrets._by_prefix


class TestSecrets:

    def test_get_secret(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200,{"value": "the value"}))
        secrets = Secrets(conn)
        value = secrets.get_secret("the_key")

        assert value == "the value"

    def test_get_non_existing_secret(self):
        conn = MockConnection()
        conn.add_response(MockResponse(404,{"error": "Secret the_key doesn't exist"}))
        secrets = Secrets(conn)
        with pytest.raises(qarnot.exceptions.SecretNotFoundException):
            _ = secrets.get_secret("the_key")

    def test_create_secret(self):
        conn = MockConnection()
        conn.add_response(MockResponse(201))
        secrets = Secrets(conn)
        value = secrets.create_secret("the key", "the value")

        assert value == "the key"

    def test_create_existing_secret(self):
        conn = MockConnection()
        conn.add_response(MockResponse(409,{"error": "Secret the_key already exists"}))
        secrets = Secrets(conn)
        with pytest.raises(qarnot.exceptions.SecretConflictException):
            _ = secrets.create_secret("the_key", "the_value")

    def test_update_secret(self):
        conn = MockConnection()
        conn.add_response(MockResponse(204))
        secrets = Secrets(conn)

        secrets.update_secret("the_key", "the_new_value")

    def test_update_non_existing_secret(self):
        conn = MockConnection()
        conn.add_response(MockResponse(404,{"error": "Secret the_key doesn't exist"}))
        secrets = Secrets(conn)

        with pytest.raises(qarnot.exceptions.SecretNotFoundException):
            _ = secrets.update_secret("the_key", "the_new_value")

    def test_delete_secret(self):
        conn = MockConnection()
        conn.add_response(MockResponse(204))
        secrets = Secrets(conn)
        
        _ = secrets.delete_secret("the_key")

    def test_list_secrets_non_recursive(self):
        # Let's imagine that these keys are registered
        # keys = [
        #     "key",
        #     "folder1/key1",
        #     "folder1/key2",
        #     "folder1/subfolder1/key1",
        #     "folder1/subfolder1/key2",
        #     "folder2/key1",
        #     "folder2/key2",
        # ]

        conn = MockConnection()
        conn.add_response(MockResponse(200, {"keys": ["key1", "key2", "subfolder1/", "subfolder2/"]}))

        secrets = Secrets(conn)
        folder1_from_server = secrets.list_secrets("folder1", False)

        assert len(folder1_from_server) == 4
        assert all([key in folder1_from_server for key in ["folder1/key1", "folder1/key2", "folder1/subfolder1/", "folder1/subfolder2/"]])

    def test_list_secrets_recursive(self):
        # Let's imagine that these keys are registered
        # keys = [
        #     "key",
        #     "folder1/key1",
        #     "folder1/key2",
        #     "folder1/subfolder1/key1",
        #     "folder1/subfolder1/key2",
        #     "folder1/subfolder1/key3",
        #     "folder1/subfolder2/key1",
        #     "folder1/subfolder2/key2",
        #     "folder2/key1",
        #     "folder2/key2",
        # ]

        conn = MockConnection()
        conn.add_response(MockResponse(200, {"keys": ["key1", "key2", "subfolder1/", "subfolder2/"]})) # search prefix "folder1"
        conn.add_response(MockResponse(200, {"keys": ["key1", "key2"]})) # search prefix "folder1/subfolder2/" (DFS traversal)
        conn.add_response(MockResponse(200, {"keys": ["key1", "key2", "key3"]})) # search prefix "folder1/subfolder1/"

        secrets = Secrets(conn)
        folder1_from_server = secrets.list_secrets("folder1", True)

        print(folder1_from_server)

        expected_secrets = [
            "folder1/key1",
            "folder1/key2",
            "folder1/subfolder1/key1",
            "folder1/subfolder1/key2",
            "folder1/subfolder1/key3",
            "folder1/subfolder2/key1",
            "folder1/subfolder2/key2"]

        assert len(folder1_from_server) == len(expected_secrets)
        assert all([key in folder1_from_server for key in expected_secrets])
