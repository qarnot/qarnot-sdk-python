"""Carbon facts prototype"""

from typing import Any, Dict
from requests import Response
from .exceptions import MissingPoolException, MissingTaskException
from . import get_url, get_url_with_param, raise_on_error, _util


class CarbonFacts(object):
    """
        Carbon facts details of a computed element
    """

    def __init__(
            self,
            energy_consumption: float = 0,
            energy_it: float = 0,
            energy_reuse: float = 0,
            carbon_footprint: float = 0,
            equivalent_dc_name: str = "",
            equivalent_dc_carbon_footprint: float = 0,
            saved_carbon_footprint_compute: float = 0,
            saved_carbon_footprint_heat: float = 0,
            saved_carbon_footprint_compute_heat: float = 0,
            saved_carbon_footprint_percent: float = 0,
            PUE: float = 0,
            ERE: float = 0,
            ERF: float = 0,
            WUE: float = 0):
        """The CarbonFacts constructor

        :param energy_consumption: the total energy consumed, in W.h
        :type energy_consumption: `float`
        :param energy_it: the energy consumed by IT, in W.h
        :type energy_it: `float`
        :param energy_reuse: the reuse heat, in W.h
        :type energy_reuse: `float`
        :param carbon_footprint: the actual carbon footprint of the computation, in gCO2eq
        :type carbon_footprint: `float`
        :param equivalent_dc_name: the name of the equivalent datacenter used for comparison
        :type equivalent_dc_name: `str`
        :param equivalent_dc_carbon_footprint: the carbon footprint the computation would generate in an equivalent DC, in gCO2eq
        :type equivalent_dc_carbon_footprint: `float`
        :param saved_carbon_footprint_compute: the carbon footprint saved by the computation part by using Qarnot instead of the equivalent DC, in gCO2eq
        :type saved_carbon_footprint_compute: `float`
        :param saved_carbon_footprint_heat: the carbon footprint saved by the heating part by using Qarnot instead of the equivalent DC, in gCO2eq
        :type saved_carbon_footprint_heat: `float`
        :param saved_carbon_footprint_compute_heat: the total carbon footprint saved by using Qarnot instead of the equivalent DC, gCO2eq
        :type saved_carbon_footprint_compute_heat: `float`
        :param saved_carbon_footprint_percent: the percentage of carbon footprint saved by using Qarnot instead of the equivalent DC, in %
        :type saved_carbon_footprint_percent: `float`
        :param PUE: the energy efficiency of the computation site
        :type PUE: `float`
        :param ERE: the energy reuse ratio of the computation site
        :type ERE: `float`
        :param ERF: the heat reuse ratio of the computation site
        :type ERF: `float`
        :param WUE: the water consumption of the computation site, in L/kWh
        :type WUE: `float`
        """
        self.energy_consumption_Wh: float = energy_consumption
        self.energy_it_Wh: float = energy_it
        self.energy_reuse_Wh: float = energy_reuse
        self.carbon_footprint_gC02eq: float = carbon_footprint
        self.equivalent_datacenter_name: str = equivalent_dc_name
        self.equivalent_dc_carbon_footprint_gC02eq: float = equivalent_dc_carbon_footprint
        self.saved_carbon_footprint_compute_gC02eq: float = saved_carbon_footprint_compute
        self.saved_carbon_footprint_heat_gC02eq: float = saved_carbon_footprint_heat
        self.saved_carbon_footprint_compute_heat_gC02eq: float = saved_carbon_footprint_compute_heat
        self.saved_carbon_footprint_percent: float = saved_carbon_footprint_percent
        self.PUE: float = PUE
        self.ERE: float = ERE
        self.ERF: float = ERF
        self.WUE: float = WUE

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a CarbonFacts from a json representation

        :param json: the json to use to create the SecretsAccessRights object.
        :type json: `Dict[str, float]`
        :returns: The created :class:`~qarnot.carbon_facts.CarbonFacts`.
        """
        if json is None:
            return None

        energy_consumption = json.get("total_consumed_energy_Wh")
        energy_it = json.get("total_energy_it_Wh")
        energy_reuse = json.get("total_reused_energy_Wh")
        carbon_footprint = json.get("qarnot_carbon_footprint")
        equivalent_datacenter_name = json.get("equivalent_datacenter_name")
        equivalent_dc_carbon_footprint = json.get("equivalent_DC_carbon_footprint")
        saved_carbon_footprint_compute = json.get("saved_carbon_footprint_compute")
        saved_carbon_footprint_heat = json.get("saved_carbon_footprint_heat")
        saved_carbon_footprint_compute_heat = json.get("saved_carbon_footprint_compute_heat")
        saved_carbon_footprint_percent = json.get("saved_carbon_footprint_percent")
        PUE = json.get("PUE")
        ERE = json.get("ERE")
        ERF = json.get("ERF")
        WUE = json.get("WUE")

        return CarbonFacts(energy_consumption, energy_it, energy_reuse, carbon_footprint, equivalent_datacenter_name,
                           equivalent_dc_carbon_footprint, saved_carbon_footprint_compute, saved_carbon_footprint_heat,
                           saved_carbon_footprint_compute_heat, saved_carbon_footprint_percent, PUE, ERE, ERF, WUE)

    def to_json(self) -> object:
        """Get a dict ready to be json packed.

        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "total_consumed_energy_Wh": self.energy_consumption_Wh,
            "total_energy_it_Wh": self.energy_it_Wh,
            "total_reused_energy_Wh": self.energy_reuse_Wh,
            "qarnot_carbon_footprint": self.carbon_footprint_gC02eq,
            "equivalent_datacenter_name": self.equivalent_datacenter_name,
            "equivalent_DC_carbon_footprint": self.equivalent_dc_carbon_footprint_gC02eq,
            "saved_carbon_footprint_compute": self.saved_carbon_footprint_compute_gC02eq,
            "saved_carbon_footprint_heat": self.saved_carbon_footprint_heat_gC02eq,
            "saved_carbon_footprint_compute_heat": self.saved_carbon_footprint_compute_heat_gC02eq,
            "saved_carbon_footprint_percent": self.saved_carbon_footprint_percent,
            "PUE": self.PUE,
            "ERE": self.ERE,
            "ERF": self.ERF,
            "WUE": self.WUE
        }


class CarbonClient(object):
    """
        Client used to interact with the Qarnot carbon API.
    """

    def __init__(self, connection, datacenter_name: str = None):
        """The CarbonClient constructor.

        :param connection: the cluster from where carbon facts are retrieved.
        :type connection: `qarnot.connection.Connection`
        :param datacenter_name: the name of the datacenter used as reference to compare carbon facts.
        :type datacenter_name: `str`
        """
        self._connection = connection
        self.reference_datacenter_name = datacenter_name

    def _get_carbon_facts_url(self, resource_type: str, uuid: str):
        if self.reference_datacenter_name is None or self.reference_datacenter_name == "":
            return get_url('%s carbon facts' % resource_type, uuid=uuid)
        return get_url_with_param('%s carbon facts' % resource_type, {'comparisonDatacenter': self.reference_datacenter_name}, uuid=uuid)

    def _get_pool_carbon_facts_raw(self, pool_id: str) -> Response:
        """Requests the carbon facts for the pool `pool_id`.

        :param pool_id: the uuid of the pool
        :type pool_id: `str`
        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.MissingPoolException: Pool was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        response = self._connection._get(self._get_carbon_facts_url('pool', pool_id))
        if response.status_code == 404:
            raise MissingPoolException(_util.get_error_message_from_http_response(response))
        raise_on_error(response)
        return response

    def get_pool_carbon_facts(self, pool_id: str) -> CarbonFacts:
        """Retrieves the carbon facts of the pool `pool_id` and parses it to a CarbonFacts object.

        :param pool_id: the uuid of the pool
        :type pool_id: `str`
        :rtype: CarbonFacts
        :raises ~qarnot.exceptions.MissingPoolException: Pool was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        raw_carbon_facts = self._get_pool_carbon_facts_raw(pool_id)
        return CarbonFacts.from_json(raw_carbon_facts.json())

    def _get_task_carbon_facts_raw(self, task_id: str) -> Response:
        """Requests the carbon facts for the task `task_id`.

        :param task_id: the uuid of the task
        :type task_id: `str`
        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.MissingTaskException: Task was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        response = self._connection._get(self._get_carbon_facts_url('task', task_id))
        if response.status_code == 404:
            raise MissingTaskException(_util.get_error_message_from_http_response(response))
        raise_on_error(response)
        return response

    def get_task_carbon_facts(self, task_id: str) -> CarbonFacts:
        """Retrieves the carbon facts of the task `task_id` and parses it to a CarbonFacts object.

        :param task_id: the uuid of the task
        :type task_id: `str`
        :rtype: CarbonFacts
        :raises ~qarnot.exceptions.MissingTaskException: Task was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        raw_carbon_facts = self._get_task_carbon_facts_raw(task_id)
        return CarbonFacts.from_json(raw_carbon_facts.json())
