# Status
import sys


class Status(object):
    """
    The status object of the running pools and tasks.

    * To retrieve the status of a pool, use:

        >>> my_pool.status


    * To retrieve the status of a task, use:

        >>> my_task.status

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.download_progress = json.get('downloadProgress')
        """:type: :class:`float`

        Resources download progress to the instances."""

        self.execution_progress = json.get('executionProgress')
        """:type: :class:`float`

        Task execution progress."""

        self.upload_progress = json.get('uploadProgress')
        """:type: :class:`float`

        Task results upload progress to the API."""

        self.instance_count = json.get('instanceCount')
        """:type: :class:`int`

        Number of running instances."""

        self.download_time = json.get('downloadTime')
        """:type: :class:`str`

        Resources download time to the instances."""

        self.download_time_sec = json.get('downloadTimeSec')
        """:type: :class:`float`

        Resources download time to the instances in seconds."""

        self.environment_time = json.get('environmentTime')
        """:type: :class:`str`

        Environment time to the instances."""

        self.environment_time_sec = json.get('environmentTimeSec')
        """:type: :class:`float`

        Environment time to the instances in seconds."""

        self.execution_time = json.get('executionTime')
        """:type: :class:`str`

        Task execution time."""

        self.execution_time_sec = json.get('executionTimeSec')
        """:type: :class:`float`

        Task execution time in seconds."""

        self.upload_time = json.get('uploadTime')
        """:type: :class:`str`

        Task results upload time to the API."""

        self.upload_time_sec = json.get('uploadTimeSec')
        """:type: :class:`float`

        Task results upload time to the API in seconds."""

        self.wall_time = json.get("wallTime")
        """:type: :class:`str`

        Wall time of the task."""

        self.wall_time_sec = json.get("wallTimeSec")
        """:type: :class:`float`

        Wall time of the task in seconds."""

        self.succeeded_range = json.get('succeededRange')
        """:type: :class:`str`

        Successful instances range."""

        self.executed_range = json.get('executedRange')
        """:type: :class:`str`

        Executed instances range."""

        self.failed_range = json.get('failedRange')
        """:type: :class:`str`

        Failed instances range."""

        self.last_update_timestamp = json.get("lastUpdateTimestamp")
        """:type: :class:`str`

        Last update time (UTC)."""

        self.execution_time_by_cpu_model = [ExecutionTimeByCpuModel(timeCpu) for timeCpu in json.get("executionTimeByCpuModel")]
        """:type: :class:`str`

        Execution time by cpu."""

        self.execution_time_ghz_by_cpu_model = [ExecutionTimeGhzByCpuModel(timeCpu) for timeCpu in json.get("executionTimeGhzByCpuModel")]
        """:type: :class:`str`

        Execution time ghz by cpu."""

        self.running_instances_info = None
        """:type: :class:`RunningInstancesInfo`

        Running instances information."""

        if 'runningInstancesInfo' in json and json.get('runningInstancesInfo') is not None:
            self.running_instances_info = RunningInstancesInfo(json.get('runningInstancesInfo'))

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

        if 'perRunningInstanceInfo' in json and json.get('perRunningInstanceInfo') is not None:
            self.per_running_instance_info = [PerRunningInstanceInfo(x) for x in json.get('perRunningInstanceInfo')]

        self.timestamp = json.get('timestamp')
        """:type: :class:`str`

        Last information update timestamp."""

        self.average_frequency_ghz = json.get('averageFrequencyGHz')
        """:type: :class:`float`

        Average Frequency in GHz."""

        self.max_frequency_ghz = json.get('maxFrequencyGHz')
        """:type: :class:`float`

        Maximum Frequency in GHz."""

        self.min_frequency_ghz = json.get('minFrequencyGHz')
        """:type: :class:`float`

        Minimum Frequency in GHz."""

        self.average_max_frequency_ghz = json.get('averageMaxFrequencyGHz')
        """:type: :class:`float`

        Average Maximum Frequency in GHz."""

        self.average_cpu_usage = json.get('averageCpuUsage')
        """:type: :class:`float`

        Average CPU Usage."""

        self.cluster_power_indicator = json.get('clusterPowerIndicator')
        """:type: :class:`float`

        Cluster Power Indicator."""

        self.average_memory_usage = json.get('averageMemoryUsage')
        """:type: :class:`float`

        Average Memory Usage."""

        self.average_network_in_kbps = json.get('averageNetworkInKbps')
        """:type: :class:`float`

        Average Network Input in Kbps."""

        self.average_network_out_kbps = json.get('averageNetworkOutKbps')
        """:type: :class:`float`

        Average Network Output in Kbps."""

        self.total_network_in_kbps = json.get('totalNetworkInKbps')
        """:type: :class:`float`

        Total Network Input in Kbps."""

        self.total_network_out_kbps = json.get('totalNetworkOutKbps')
        """:type: :class:`float`

        Total Network Output in Kbps."""

        self.snapshot_results = json.get('snapshotResults')
        """:type: :class:`float`

        Total Network Output in Kbps."""
        self.running_core_count_by_cpu_model = json.get('runningCoreCountByCpuModel')
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
        self.phase = json.get('phase')
        """:type: :class:`str`

        Instance phase."""

        self.instance_id = json.get('instanceId')
        """:type: :class:`int`

        Instance number."""

        self.max_frequency_ghz = json.get('maxFrequencyGHz')
        """:type: :class:`float`

        Maximum CPU frequency in GHz."""

        self.current_frequency_ghz = json.get('currentFrequencyGHz')
        """:type: :class:`float`

        Current CPU frequency in GHz."""

        self.cpu_usage = json.get('cpuUsage')
        """:type: :class:`float`

        Current CPU usage."""

        self.max_memory_mb = json.get('maxMemoryMB')
        """:type: :class:`int`

        Maximum memory size in MB."""

        self.current_memory_mb = json.get('currentMemoryMB')
        """:type: :class:`int`

        Current memory size in MB."""

        self.memory_usage = json.get('memoryUsage')
        """:type: :class:`float`

        Current memory usage."""

        self.network_in_kbps = json.get('networkInKbps')
        """:type: :class:`float`

        Network Input in Kbps."""

        self.network_out_kbps = json.get('networkOutKbps')
        """:type: :class:`float`

        Network Output in Kbps."""

        self.progress = json.get('progress')
        """:type: :class:`float`

        Instance progress."""

        self.execution_time_sec = json.get('executionTimeSec')
        """:type: :class:`float`

        Instance execution time in seconds."""

        self.execution_time_ghz = json.get('executionTimeGHz')
        """:type: :class:`float`

        Instance execution time GHz"""

        self.cpu_model = json.get('cpuModel')
        """:type: :class:`str`

        CPU model"""

        self.execution_attempt_count = json.get('executionAttemptCount', 0)
        """:type: :class:`int`

        Number of execution attempt of an instance, (manly in case of preemption)."""

        self.active_forward = []
        """type: list(:class:`TaskActiveForward`)

        Active forwards list."""

        if 'activeForwards' in json:
            self.active_forward = [TaskActiveForward(x) for x in json.get('activeForwards')]

        self.vpn_connections = []
        """type: list(:class:`TaskVpnConnection`)

        Vpn connection list."""

        if "vpnConnections" in json:
            self.vpn_connections = [TaskVpnConnection(x) for x in json.get("vpnConnections")]

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
        self.application_port = json.get('applicationPort')
        """:type: :class:`int`

        Application Port."""

        self.forwarder_port = json.get('forwarderPort')
        """:type: :class:`int`

        Forwarder Port."""

        self.forwarder_host = json.get('forwarderHost')
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


class ExecutionTimeByCpuModel:
    """Execution time by Cpu model

    .. note:: Read-only class
    """

    def __init__(self, json):
        self.model = json.get("model")
        """:type: :class:`str`

        Cpu Model."""

        self.time = json.get("time")
        """:type: :class:`int`

        Execution time in seconds."""

        self.core = json.get("core")
        """:type: :class:`int`

        CPU Cores."""

    def __repr__(self):
        return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())


class ExecutionTimeGhzByCpuModel:
    """Execution time Gtz by Cpu model

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.model = json.get("model")
        """:type: :class:`str`

        Cpu Model."""

        self.time_ghz = json.get("timeGhz")
        """:type: :class:`float`

        Execution time in Gigahertz."""

        self.clock_ratio = json.get("clockRatio")
        """:type: :class:`int`

        Cpu clock ratio."""

        self.core = json.get("core")
        """:type: :class:`int`

        CPU Cores."""

    def __repr__(self):
        return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())


class TaskVpnConnection(object):
    """ Vpn Connection Information

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.node_ip_address_cidr = json.get('nodeIPAddressCidr')
        """:type: :class:`str`

        Vpn classless inter-domain routing address."""

        self.vpn_name = json.get('vpnName')
        """:type: :class:`str`

        Vpn name."""

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member
