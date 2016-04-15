TrueSight Pulse vmware Plugin
=============================

Collects metrics from the virtual machines using the vSphere SDK.

### Prerequisites

|     OS    | Linux | Windows | SmartOS | OS X |
|:----------|:-----:|:-------:|:-------:|:----:|
| Supported |   v   |    v    |    -    |  v   |

* Python 2.7, 3.0, 3.1 or 3.4
* This plugin is compatible with vmware vSphere	4.1, 5.0, 5.1 & 5.5.

#### TrueSight Pulse Meter versions v4.2.4 or later

- To install new meter go to Settings->Installation or [see instructions](https://help.boundary.com/hc/en-us/sections/200634331-Installation).
- To upgrade the meter to the latest version - [see instructions](https://help.boundary.com/hc/en-us/articles/201573102-Upgrading-the-Boundary-Meter).

### Plugin Configuration Fields

|Field Name        |Description                                                          |
|:-----------------|:--------------------------------------------------------------------|
|Host              |The vCenter hostname                                                 |
|Port              |The vCenter port                                                     |
|Username          |The username required to connect to vCenter                          |
|Password          |The password required to connect to vCenter                          |
|Poll Interval     |How often (in milliseconds) to poll for metrics                      |
|Discovery Interval|How often (in milliseconds) to discover the virtual machines         |
|Max Depth         |Max depth to traverse vCenter to discover VMs                        |
|Max Sample Size   |Maximum number of values to limit the amount of data to be collected |

### Metrics Collected

|Metric Name                           |Description                                    |
|:-------------------------------------|:----------------------------------------------|
|VMWARE_SYSTEM_CPU_USAGE_AVERAGE       |CPU Average Utilization                        |
|VMWARE_SYSTEM_CPU_USAGE_MAXIMUM       |CPU Usage Maximum                              |
|VMWARE_SYSTEM_MEMORY_ACTIVE_MAXIMUM   |Memory Maximum Active                          |
|VMWARE_SYSTEM_MEMORY_CONSUMED_AVERAGE |Memory Consumed Average                        |
|VMWARE_SYSTEM_DISK_READ_AVERAGE       |Disk Read Average                              |
|VMWARE_SYSTEM_DISK_WRITE_AVERAGE      |Disk Write Average                             |
|VMWARE_SYSTEM_NETWORK_BYTES_TX_AVERAGE|Network Bytes Trasnferred Average              |
|VMWARE_SYSTEM_NETWORK_BYTES_RX_AVERAGE|Network Bytes Received Average                 |
|VMWARE_SYSTEM_NETWORK_PACKETS_TX_SUM  |Network Packets Transferred Sum                |
|VMWARE_SYSTEM_NETWORK_PACKETS_RX_SUM  |Network Packets Received Sum                   | 

### Dashboards

- Virtual Machines Summary

### References

https://github.com/vmware/pyvmomi/tree/master/docs


