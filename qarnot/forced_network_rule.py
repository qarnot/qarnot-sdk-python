
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
            to_payload: Optional[bool] = None):
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
        :returns: The created :class:`~qarnot.retry_settings.ForcedNetworkRule`
        """

        inbound: bool = bool(json["inbound"])
        proto: str = str(json["proto"])

        port: str = None
        if 'port' in json:
            port = str(json["port"])

        to: str = None
        if 'to' in json:
            to = str(json["to"])

        public_host: str = None
        if 'public_host' in json:
            public_host = str(json["public_host"])

        public_port: str = None
        if 'public_port' in json:
            public_port = str(json["public_port"])

        forwarder: str = None
        if 'forwarder' in json:
            forwarder = str(json["forwarder"])

        priority: str = None
        if 'priority' in json:
            priority = str(json["priority"])

        description: str = None
        if 'description' in json:
            description = str(json["description"])

        to_qbox: Optional[bool] = None
        if 'to_qbox' in json:
            to_qbox = bool(json["to_qbox"])

        to_payload: Optional[bool] = None
        if 'to_payload' in json:
            to_payload = bool(json["to_payload"])

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
            to_payload)

    def to_json(self):
        result: Dict[str, Union[str, bool]] = {
            "inbound": self.inbound,
            "proto": self.proto,
        }

        if self.port is not None:
            result["port"] = self.port

        if self.to is not None:
            result["to"] = self.to

        if self.public_host is not None:
            result["public_host"] = self.public_host

        if self.public_port is not None:
            result["public_port"] = self.public_port

        if self.forwarder is not None:
            result["forwarder"] = self.forwarder

        if self.priority is not None:
            result["priority"] = self.priority

        if self.description is not None:
            result["description"] = self.description

        if self.to_qbox is not None:
            result["to_qbox"] = self.to_qbox

        if self.to_payload is not None:
            result["to_payload"] = self.to_payload

        return result
