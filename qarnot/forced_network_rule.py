
from typing import Dict, Optional, Union


class ForcedNetworkRule(object):
    """Forced Network Rule

    .. note:: For internal usage only
    """

    def __init__(
            self,
            inbound: bool,
            proto: str,
            port: str = None,
            to: str = None,
            public_host: str = None,
            public_port: str = None,
            forwarder: str = None,
            priority: str = None,
            description: str = None,
            to_qbox: Optional[bool] = None,
            to_payload: Optional[bool] = None,
            name: str = None,
            application_type: str = None):

        self.name = name
        """:type: :class:`str`

        Name of the associated rule."""
        self.application_type = application_type
        """:type: :class:`str`

        Application layer protocol used / hint about it (e.g. ssh, http, https...)."""
        self.inbound = inbound
        """:type: :class:`bool`

        Whether it concerns inbound or outbound traffic."""

        self.proto = proto
        """:type: :class:`str`

        Allowed protocol (tcp or udp)."""

        self.port = port
        """:type: :class:`str`

        Inbound port on the running instance."""

        self.to = to
        """:type: :class:`str`

        For inbound rules, allowed source address."""

        self.public_host = public_host
        """:type: :class:`str`

        For outbound rules, allowed destination address."""

        self.public_port = public_port
        """:type: :class:`str`

        Outbound port allowed in the destination address."""

        self.forwarder = forwarder
        """:type: :class:`str`

        Type of forwarder used."""

        self.priority = priority
        """:type: :class:`str`

        Priority of the rule."""

        self.description = description
        """:type: :class:`str`

        Description of the rule to help debugging."""

        self.to_qbox = to_qbox
        """:type: :class:`bool`

        Whether the network endpoint to access is on the qbox."""

        self.to_payload = to_payload
        """:type: :class:`bool`

        Whether the network endpoint to access is in the payload."""

    @classmethod
    def from_json(cls, json: Dict[str, Union[str, bool]]):
        """Create the forced network rule from json.

        :param dict json: Dictionary representing the forced network rule
        :returns: The created :class:`~qarnot.forced_network_rule.ForcedNetworkRule`
        """

        name: str = None
        if 'name' in json:
            name = str(json.get("name"))

        application_type: str = None
        if 'applicationType' in json:
            application_type = str(json.get("applicationType"))

        inbound: bool = bool(json.get("inbound"))
        proto: str = str(json.get("proto"))

        port: str = None
        if 'port' in json:
            port = str(json.get("port"))

        to: str = None
        if 'to' in json:
            to = str(json.get("to"))

        public_host: str = None
        if 'publicHost' in json:
            public_host = str(json.get("publicHost"))

        public_port: str = None
        if 'publicPort' in json:
            public_port = str(json.get("publicPort"))

        forwarder: str = None
        if 'forwarder' in json:
            forwarder = str(json.get("forwarder"))

        priority: str = None
        if 'priority' in json:
            priority = str(json.get("priority"))

        description: str = None
        if 'description' in json:
            description = str(json.get("description"))

        to_qbox: Optional[bool] = None
        if 'toQBox' in json:
            to_qbox = bool(json.get("toQBox"))

        to_payload: Optional[bool] = None
        if 'toPayload' in json:
            to_payload = bool(json.get("toPayload"))

        return ForcedNetworkRule(
            inbound,
            proto,
            port,
            to,
            public_host,
            public_port,
            forwarder,
            priority,
            description,
            to_qbox,
            to_payload,
            name,
            application_type)

    def to_json(self):
        result: Dict[str, Union[str, bool]] = {
            "inbound": self.inbound,
            "proto": self.proto,
        }

        if self.name is not None:
            result["name"] = self.name

        if self.application_type is not None:
            result["applicationType"] = self.application_type

        if self.port is not None:
            result["port"] = self.port

        if self.to is not None:
            result["to"] = self.to

        if self.public_host is not None:
            result["publicHost"] = self.public_host

        if self.public_port is not None:
            result["publicPort"] = self.public_port

        if self.forwarder is not None:
            result["forwarder"] = self.forwarder

        if self.priority is not None:
            result["priority"] = self.priority

        if self.description is not None:
            result["description"] = self.description

        if self.to_qbox is not None:
            result["toQBox"] = self.to_qbox

        if self.to_payload is not None:
            result["toPayload"] = self.to_payload

        return result
