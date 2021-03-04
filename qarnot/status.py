# Status
import sys


class Status(object):
    """Status
    The status object of the running pools and tasks.
    To retrieve the status of a pool, use:
        * my_pool.status
    To retrieve the status of a task, use:
        * my_task.status

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.download_progress = json['downloadProgress']
        """:type: :class:`float`

        Resources download progress to the instances."""

        self.execution_progress = json['executionProgress']
        """:type: :class:`float`

        Task execution progress."""

        self.upload_progress = json['uploadProgress']
        """:type: :class:`float`

        Task results upload progress to the API."""

        self.instance_count = json['instanceCount']
        """:type: :class:`int`

        Number of running instances."""

        self.download_time = json['downloadTime']
        """:type: :class:`str`

        Resources download time to the instances."""

        self.download_time_sec = json['downloadTimeSec']
        """:type: :class:`float`

        Resources download time to the instances in seconds."""

        self.environment_time = json['environmentTime']
        """:type: :class:`str`

        Environment time to the instances."""

        self.environment_time_sec = json['environmentTimeSec']
        """:type: :class:`float`

        Environment time to the instances in seconds."""

        self.execution_time = json['executionTime']
        """:type: :class:`str`

        Task execution time."""

        self.execution_time_sec = json['executionTimeSec']
        """:type: :class:`float`

        Task execution time in seconds."""

        self.upload_time = json['uploadTime']
        """:type: :class:`str`

        Task results upload time to the API."""

        self.upload_time_sec = json['uploadTimeSec']
        """:type: :class:`float`

        Task results upload time to the API in seconds."""

        self.wall_time = json["wallTime"]
        """:type: :class:`str`

        Wall time of the task."""

        self.wall_time_sec = json["wallTimeSec"]
        """:type: :class:`float`

        Wall time of the task in seconds."""

        self.succeeded_range = json['succeededRange']
        """:type: :class:`str`

        Successful instances range."""

        self.executed_range = json['executedRange']
        """:type: :class:`str`

        Executed instances range."""

        self.failed_range = json['failedRange']
        """:type: :class:`str`

        Failed instances range."""

        self.running_instances_info = None
        """:type: :class:`RunningInstancesInfo`

        Running instances information."""

        if 'runningInstancesInfo' in json and json['runningInstancesInfo'] is not None:
            self.running_instances_info = RunningInstancesInfo(json['runningInstancesInfo'])

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member


class RunningInstancesInfo(object):
    """Running Instances Information

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.per_running_instance_info = []
        """:type: list(:class:`PerRunningInstanceInfo`)

        Per running instances information."""

        if 'perRunningInstanceInfo' in json and json['perRunningInstanceInfo'] is not None:
            self.per_running_instance_info = [PerRunningInstanceInfo(x) for x in json['perRunningInstanceInfo']]

        self.timestamp = json['timestamp']
        """:type: :class:`str`

        Last information update timestamp."""

        self.average_frequency_ghz = json['averageFrequencyGHz']
        """:type: :class:`float`

        Average Frequency in GHz."""

        self.max_frequency_ghz = json['maxFrequencyGHz']
        """:type: :class:`float`

        Maximum Frequency in GHz."""

        self.min_frequency_ghz = json['minFrequencyGHz']
        """:type: :class:`float`

        Minimum Frequency in GHz."""

        self.average_max_frequency_ghz = json['averageMaxFrequencyGHz']
        """:type: :class:`float`

        Average Maximum Frequency in GHz."""

        self.average_cpu_usage = json['averageCpuUsage']
        """:type: :class:`float`

        Average CPU Usage."""

        self.cluster_power_indicator = json['clusterPowerIndicator']
        """:type: :class:`float`

        Cluster Power Indicator."""

        self.average_memory_usage = json['averageMemoryUsage']
        """:type: :class:`float`

        Average Memory Usage."""

        self.average_network_in_kbps = json['averageNetworkInKbps']
        """:type: :class:`float`

        Average Network Input in Kbps."""

        self.average_network_out_kbps = json['averageNetworkOutKbps']
        """:type: :class:`float`

        Average Network Output in Kbps."""

        self.total_network_in_kbps = json['totalNetworkInKbps']
        """:type: :class:`float`

        Total Network Input in Kbps."""

        self.total_network_out_kbps = json['totalNetworkOutKbps']
        """:type: :class:`float`

        Total Network Output in Kbps."""

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member


class PerRunningInstanceInfo(object):
    """Per Running Instance Information

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.phase = json['phase']
        """:type: :class:`str`

        Instance phase."""

        self.instance_id = json['instanceId']
        """:type: :class:`int`

        Instance number."""

        self.max_frequency_ghz = json['maxFrequencyGHz']
        """:type: :class:`float`

        Maximum CPU frequency in GHz."""

        self.current_frequency_ghz = json['currentFrequencyGHz']
        """:type: :class:`float`

        Current CPU frequency in GHz."""

        self.cpu_usage = json['cpuUsage']
        """:type: :class:`float`

        Current CPU usage."""

        self.max_memory_mb = json['maxMemoryMB']
        """:type: :class:`int`

        Maximum memory size in MB."""

        self.current_memory_mb = json['currentMemoryMB']
        """:type: :class:`int`

        Current memory size in MB."""

        self.memory_usage = json['memoryUsage']
        """:type: :class:`float`

        Current memory usage."""

        self.network_in_kbps = json['networkInKbps']
        """:type: :class:`float`

        Network Input in Kbps."""

        self.network_out_kbps = json['networkOutKbps']
        """:type: :class:`float`

        Network Output in Kbps."""

        self.progress = json['progress']
        """:type: :class:`float`

        Instance progress."""

        self.execution_time_sec = json['executionTimeSec']
        """:type: :class:`float`

        Instance execution time in seconds."""

        self.execution_time_ghz = json['executionTimeGHz']
        """:type: :class:`float`

        Instance execution time GHz"""

        self.cpu_model = json['cpuModel']
        """:type: :class:`str`

        CPU model"""

        self.active_forward = []
        """type: list(:class:`TaskActiveForward`)

        Active forwards list."""

        if 'activeForwards' in json:
            self.active_forward = [TaskActiveForward(x) for x in json['activeForwards']]

        self.vpn_connections = []
        """type: list(:class:`TaskVpnConnection`)

        Vpn connection list."""

        if "vpnConnections" in json:
            self.vpn_connections = [TaskVpnConnection(x) for x in json["vpnConnections"]]

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member


class TaskActiveForward(object):
    """Task Active Forward

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.application_port = json['applicationPort']
        """:type: :class:`int`

        Application Port."""

        self.forwarder_port = json['forwarderPort']
        """:type: :class:`int`

        Forwarder Port."""

        self.forwarder_host = json['forwarderHost']
        """:type: :class:`str`

        Forwarder Host."""

        self.bind_address = json.get('bindAddress')
        """:type: :class:`str`

        Bind address of the listening socket on the forwarder host."""

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member


class TaskVpnConnection(object):
    """ Vpn Connection Information

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.node_ip_address_cidr = json['nodeIPAddressCidr']
        """:type: :class:`str`

        Vpn classless inter-domain routing address."""

        self.vpn_name = json['vpnName']
        """:type: :class:`str`

        Vpn name."""

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member
