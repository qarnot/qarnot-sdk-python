import copy

default_json_task: dict = {
    "uuid":  "e4af4f1f-32ae-4e78-8d1b-1b9d8260d78b",
    "name":  "test",
    "shortname":  "e4af4f1f-32ae-4e78-8d1b-1b9d8260d78b",
    "profile":  "docker-batch",
    "poolUuid":  None,
    "jobUuid":  None,
    "progress":  100,
    "runningInstanceCount":  0,
    "runningCoreCount":  0,
    "executionTime":  "00:28:04",
    "wallTime":  "00:30:27",
    "state":  "Success",
    "previousState":  "UploadingResults",
    "instanceCount":  1,
    "stateTransitionTime":  "2021-07-20T16:40:13Z",
    "previousStateTransitionTime":  "2021-07-20T16:40:07Z",
    "lastModified":  "2021-07-20T16:40:13Z",
    "creationDate":  "2021-07-20T16:09:43Z",
    "endDate":  "2021-07-20T16:40:13Z",
    "waitForPoolResourcesSynchronization":  None,
    "resourceBuckets":  [
        "resource"
    ],
    "advancedResourceBuckets":  [
    ],
    "resultBucket":  "result",
    "errors":  [
    ],
    "completedInstances":  [
        {
            "results":  [
                "s3://storage.qarnot.com/result/data-result.txt"
            ],
            "instanceId":  0,
            "wallTimeSec":  1827.2825,
            "execTimeSec":  1684,
            "execTimeSecGHz":  5385.8447,
            "peakMemoryMB":  0,
            "state":  "Success",
            "error":  None,
            "cpuModel":  "AMD Ryzen 7 2700 Eight-Core Processor",
            "coreCount":  16,
            "clockRatio":  0.999,
            "averageGHz":  3.198245,
            "executionAttemptCount": 43,
        }
    ],
    "status":  {
        "timestamp":  "0001-01-01T00:00:00Z",
        "lastUpdateTimestamp":  "0001-01-01T00:00:00Z",
        "downloadProgress":  0,
        "executionProgress":  100,
        "uploadProgress":  100,
        "instanceCount":  0,
        "downloadTime":  "00:00:00",
        "downloadTimeSec":  0,
        "environmentTime":  "00:01:02",
        "environmentTimeSec":  62,
        "executionTime":  "00:28:04",
        "executionTimeSec":  1684,
        "executionTimeByCpuModel":  [
            {
                "model":  "AMD Ryzen 7 2700 Eight-Core Processor",
                "time":  1684,
                "core":  16
            }
        ],
        "executionTimeGhzByCpuModel":  [
            {
                "model":  "AMD Ryzen 7 2700 Eight-Core Processor",
                "timeGhz":  5385.8447265625,
                "clockRatio":  0.999,
                "core":  16
            }
        ],
        "uploadTime":  "00:00:04",
        "uploadTimeSec":  4,
        "wallTime":  "00:30:27",
        "wallTimeSec":  1827,
        "succeededRange":  "0",
        "executedRange":  "0",
        "failedRange":  "",
        "startedOnceRange":  "0",
        "runningInstancesInfo":  {
            "perRunningInstanceInfo":  [
            ],
            "snapshotResults":  [
            ],
            "timestamp":  "0001-01-01T00:00:00Z",
            "averageFrequencyGHz":  0,
            "maxFrequencyGHz":  0,
            "minFrequencyGHz":  0,
            "averageMaxFrequencyGHz":  0,
            "averageCpuUsage":  0,
            "clusterPowerIndicator":  1,
            "averageMemoryUsage":  0,
            "averageNetworkInKbps":  0,
            "averageNetworkOutKbps":  0,
            "totalNetworkInKbps":  0,
            "totalNetworkOutKbps":  0,
            "runningCoreCountByCpuModel":  [
            ]
        }
    },
    "snapshotInterval":  0,
    "resultsCount":  1,
    "constants":  [
        {
            "key":  "DOCKER_REPO",
            "value":  "qlab/pandas"
        },
        {
            "key":  "DOCKER_TAG",
            "value":  "latest"
        },
        {
            "key":  "DOCKER_CMD",
            "value":  "python3 launch.py"
        }
    ],
    "tags":  [
    ],
    "dependencies":  None,
    "autoDeleteOnCompletion":  False,
    "completionTimeToLive":  "00:00:00",
    "maxRetriesPerInstance":  0,
    "privileges":  {
        "exportApiAndStorageCredentialsInEnvironment": False
    }
}


task_with_running_instances = copy.deepcopy(default_json_task)
task_with_running_instances.update({
    "state":  "FullyExecuting",
    "previousState":  "FullyDispatched",
})


task_with_running_instances['status']['runningInstancesInfo']['perRunningInstanceInfo'] = [
        {
            "phase": "execution",
            "instanceId": 0,
            "maxFrequencyGHz": 3.4,
            "currentFrequencyGHz": 3.4,
            "cpuUsage": 48.75,
            "maxMemoryMB": 359,
            "currentMemoryMB": 356,
            "networkInKbps": 0,
            "networkOutKbps": 3,
            "progress": 0,
            "executionTimeSec": 994,
            "executionTimeGHz": 3335.2075,
            "cpuModel": "AMD Ryzen 7 1700X Eight-Core Processor",
            "coreCount": 16,
            "executionAttemptCount": 1,
            "activeForwards": [
            ],
            "vpnConnections": [
            ],
            "memoryUsage": 0.9916434,
            "clockRatio": 1
        },
        {
            "phase": "execution",
            "instanceId": 1,
            "maxFrequencyGHz": 3.901,
            "currentFrequencyGHz": 3.901,
            "cpuUsage": 0,
            "maxMemoryMB": 313,
            "currentMemoryMB": 310,
            "networkInKbps": 0,
            "networkOutKbps": 0,
            "progress": 0,
            "executionTimeSec": 992,
            "executionTimeGHz": 3868.6113,
            "cpuModel": "Intel(R) Core(TM) i7-3770K CPU @ 3.50GHz",
            "coreCount": 4,
            "executionAttemptCount": 2,
            "activeForwards": [
            ],
            "vpnConnections": [
            ],
            "memoryUsage": 0.99041533,
            "clockRatio": 1
        }
    ]
