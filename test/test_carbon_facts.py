
import pytest
import qarnot
from qarnot.carbon_facts import CarbonClient, CarbonFacts
from test.mock_carbon_facts import default_json_carbon_facts
from test.mock_connection import MockConnection, MockResponse, GetRequest


class TestCarbonFacts:

    def test_get_carbon_facts_of_pool(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200, default_json_carbon_facts))
        carbon_client = CarbonClient(conn)
        carbon_facts = carbon_client.get_pool_carbon_facts("pool_id")

        assert carbon_facts is not None
        assert isinstance(carbon_facts, CarbonFacts)
        assert carbon_facts.energy_consumption_Wh == 1432
        assert carbon_facts.energy_it_Wh == 1234
        assert carbon_facts.energy_reuse_Wh == 1232
        assert carbon_facts.carbon_footprint_gC02eq == 1042
        assert carbon_facts.equivalent_datacenter_name == "default-datacenter"
        assert carbon_facts.equivalent_dc_carbon_footprint_gC02eq == 3600
        assert carbon_facts.saved_carbon_footprint_compute_gC02eq == 1402
        assert carbon_facts.saved_carbon_footprint_heat_gC02eq == 1156
        assert carbon_facts.saved_carbon_footprint_compute_heat_gC02eq == 2558
        assert carbon_facts.saved_carbon_footprint_percent == 71
        assert carbon_facts.PUE == 1.1
        assert carbon_facts.ERE == 0.8
        assert carbon_facts.ERF == 0.9
        assert carbon_facts.WUE == 0.1

    def test_get_carbon_facts_of_non_existing_pool(self):
        conn = MockConnection()
        conn.add_response(MockResponse(404,{"message": "Pool not found"}))
        carbon_client = CarbonClient(conn)
        with pytest.raises(qarnot.exceptions.MissingPoolException):
            _ = carbon_client.get_pool_carbon_facts("pool_id")

    def test_get_carbon_facts_of_task(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200, default_json_carbon_facts))
        carbon_client = CarbonClient(conn)
        carbon_facts = carbon_client.get_task_carbon_facts("task_id")

        assert carbon_facts is not None
        assert isinstance(carbon_facts, CarbonFacts)
        assert carbon_facts.energy_consumption_Wh == 1432
        assert carbon_facts.energy_it_Wh == 1234
        assert carbon_facts.energy_reuse_Wh == 1232
        assert carbon_facts.carbon_footprint_gC02eq == 1042
        assert carbon_facts.equivalent_datacenter_name == "default-datacenter"
        assert carbon_facts.equivalent_dc_carbon_footprint_gC02eq == 3600
        assert carbon_facts.saved_carbon_footprint_compute_gC02eq == 1402
        assert carbon_facts.saved_carbon_footprint_heat_gC02eq == 1156
        assert carbon_facts.saved_carbon_footprint_compute_heat_gC02eq == 2558
        assert carbon_facts.saved_carbon_footprint_percent == 71
        assert carbon_facts.PUE == 1.1
        assert carbon_facts.ERE == 0.8
        assert carbon_facts.ERF == 0.9
        assert carbon_facts.WUE == 0.1

    def test_get_carbon_facts_of_non_existing_task(self):
        conn = MockConnection()
        conn.add_response(MockResponse(404,{"message": "Pool not found"}))
        carbon_client = CarbonClient(conn)
        with pytest.raises(qarnot.exceptions.MissingTaskException):
            _ = carbon_client.get_task_carbon_facts("task_id")

    def test_get_carbon_facts_with_specific_reference_datacenter(self):
        conn = MockConnection()
        carbon_client = CarbonClient(conn, "custom_datacenter")

        carbon_facts = carbon_client.get_pool_carbon_facts("pool_id")
        assert conn.requests[0].uri == qarnot.get_url('pool carbon facts', uuid='pool_id') + "?comparisonDatacenter=custom_datacenter"

        carbon_facts = carbon_client.get_task_carbon_facts("task_id")
        assert conn.requests[1].uri == qarnot.get_url('task carbon facts', uuid='task_id') + "?comparisonDatacenter=custom_datacenter"

