__author__ = 'gokumar'

"""
DataCollector that collects the VMs' details/performance metrics from vCenter
"""

import atexit
from dateutil import parser
from dateutil import tz
import sys
import datetime
from requests.packages import urllib3
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

from modules import util

if sys.version_info > (2, 7, 9):
    import ssl

params = None
metrics = None
counters  = None

class VMWare():
    """
    VMWare class has all the necessary methods that discovers, monitors and pushes metrics to the Platform Shell. It
    connects to all the vCenters configured in vmware.yaml file.
    FIXME: Currently, discovers and monitors only VMs. It should be enhanced to discover and monitor other entities of
    vCenter at a later stage
    """

    # Holds all the VMs' instanceuuid that are discovered for each of the vCenter. Going ahead it would hold all the
    # other managed objects of vCenter that would be monitored.
    mors = {}

    # All vCenters' names defined in the vmware.yaml configuration would be loaded into this array
    vcenters = []

    # All vCenters defined in the vmware.yaml configuration would be loaded into this array
    vmware_instances_cfg = {}

    # pyvmomi provides a managed object that is a singleton root object of the inventory on vCenter server and servers
    # running on standalone host agents.
    # One such instance for every vCenter defined in the configuration is fetched and stored in this dictionary that
    # will be used for discovering various managed objects and querying various metrics for each managed object.
    service_instances = {}

    def __init__(self):
        """
        Initialization responsible for fetching service instance objects for each vCenter instance
        pyvmomi has some security checks enabled by default from python 2.7.9 onward to connect to vCenter.
        """
        # FIXME: For now it is being disabled automatically for Python 2.7.9 and beyond, going ahead, certificates need..
        # FIXME: ..to be provided as part of configuration that can be used to make secured connection with vCenter

        global params
        global metrics
        global counters

        params = util.parse_params()
        metrics = util.parse_metrics()
        counters = util.parse_counters()

        self.needed_metrics = {}
        self.configured_metrics = {}
        self.refresh_rates = {}

        for k, v in metrics.items():
            self.configured_metrics.update({util.get_counter(k): v})

        if sys.version_info > (2, 7, 9) and sys.version_info < (3, 0, 0):
            # https://www.python.org/dev/peps/pep-0476/
            # Look for 'Opting out' section in this that talks about disabling the certificate verification

            # Following line helps to disable globally
            ssl._create_default_https_context = ssl._create_unverified_context
        #
        # Disabling the security warning message, as the certificate verification is disabled
        urllib3.disable_warnings()

        context = None
        # context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        # context.verify_mode = ssl.CERT_NONE

        if sys.version_info > (3, 0, 0):
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3

        try:
            for instance in params['items']:
                if not instance['host'] in VMWare.vcenters:
                    VMWare.vmware_instances_cfg[instance['host']] = instance
                    VMWare.vcenters.append(instance['host'])

                    if instance['port']:
                        service_instance = connect.SmartConnect(host=instance['host'],
                                                                user=instance['username'],
                                                                pwd=instance['password'],
                                                                port=int(instance['port']))
                    else:
                        service_instance = connect.SmartConnect(host=instance['host'],
                                                                user=instance['username'],
                                                                pwd=instance['password'])
                    atexit.register(connect.Disconnect, service_instance)
                    VMWare.service_instances[instance['host']] = service_instance
                    self._cache_metrics_metadata(instance['host'])
        except KeyError:
            util.report_event("Error", "Improper param.json", None)

    def discovery(self):
        """
        This method is responsible to discover all the entities that belongs to all the vCenter instances that are
        configured
        """

        for vcenter_name, value in VMWare.vmware_instances_cfg.items():
            service_instance = VMWare.service_instances[vcenter_name]
            content = service_instance.RetrieveContent()
            children = content.rootFolder.childEntity
            for child in children:
                if hasattr(child, 'vmFolder'):
                    datacenter = child
                else:
                    # some other non-datacenter type object
                    continue

                vm_folder = datacenter.vmFolder
                vm_list = vm_folder.childEntity
                for virtual_machine in vm_list:
                    self.create_vms(vcenter_name, virtual_machine, value['maxdepth'])

    def create_vms(self, vcenter_name, virtual_machine, depth=1):
        """
        This method is responsible to create VM objects by traversing recursively through the entire tree and also make
        device create requests to Platform Shell along with relationships creation requests
        """

        if hasattr(virtual_machine, 'childEntity'):
            if depth > 0 :
                return
            vm_list = virtual_machine.childEntity
            for c in vm_list:
                self.create_vms(vcenter_name, c, depth - 1)
            return

        class_type = type(virtual_machine).__name__

        # If the type of the discovered entity is VirtualMachine, make device creation request to the Platform Shell
        # for this VM along with relationship creation request. Also, push this VM's instanceuuid in the mors[] that
        # would be used during metric collection process.
        if class_type == 'vim.VirtualMachine' and virtual_machine.config and (not virtual_machine.config.template):
            uuid = virtual_machine.config.instanceUuid
            name = virtual_machine.config.name

            if vcenter_name not in VMWare.mors:
                VMWare.mors[vcenter_name] = []

            if uuid not in VMWare.mors[vcenter_name]:
                VMWare.mors[vcenter_name].append(uuid)
                # log.debug('Creating VM: ' + virtual_machine.config.name)
                service_instance = VMWare.service_instances[vcenter_name]
                summary = service_instance.content.perfManager.QueryPerfProviderSummary(entity=virtual_machine)
                refresh_rate = 20
                if summary:
                    if summary.refreshRate:
                        refresh_rate = summary.refreshRate

                self.refresh_rates[uuid] = refresh_rate

                available_metric_ids = service_instance.content.perfManager.QueryAvailablePerfMetric(
                    entity=virtual_machine)

                self.needed_metrics[uuid] = self._compute_needed_metrics(vcenter_name, available_metric_ids)

    def collect(self, vcenter_name):
        """
        This method is responsible to traverse through the mors[] and query metrics for each of the managed object that
        is discovered for all the vCenters.
        """

        for instance_key, service_instance in VMWare.service_instances.items():
            content = service_instance.RetrieveContent()
            search_index = service_instance.content.searchIndex

            vcenter = VMWare.vmware_instances_cfg[vcenter_name]

            polling_interval = vcenter['pollInterval']

            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(seconds=polling_interval / 1000)
            print(str(start_time) + "<<<<<<<<<<<<<<>>>>>>>>>>" + str(end_time))

            try:
                if instance_key in VMWare.mors:
                    for uuid in VMWare.mors[instance_key]:
                        vm = search_index.FindByUuid(None, uuid, True, True)
                        if vm is not None:
                            if uuid in self.needed_metrics:
                                needed_metric_ids = self.needed_metrics[uuid]
                                if uuid in self.refresh_rates:
                                    refresh_rate = self.refresh_rates[uuid]

                                    query = vim.PerformanceManager.QuerySpec(intervalId=refresh_rate,
									     maxSample=int(polling_interval / 1000),
                                                                             entity=vm,
                                                                             metricId=needed_metric_ids,
                                                                             startTime=start_time,
                                                                             endTime=end_time)
                                    result = content.perfManager.QueryPerf(querySpec=[query])
                                    #print result
                                    self._parse_result_and_publish(instance_key, vm.config.name, result)
                                else:
                                    print("Can't believe, refresh rates does not have " + uuid)
                            else:
                                print("Can't believe, needed metrics does not have " + uuid)

            except vmodl.MethodFault as error:
                util.report_event("Error", error, None)

    def _parse_result_and_publish(self, instance_key, uuid, result):
        """
        This method is responsible to push the queried metrics to the Platform Shell
        """
        if result and len(result) == 1:
            samples = result[0].sampleInfo
            values = result[0].value
            samples_size = len(samples)
            if samples_size > 0:
                for indx in range(0, samples_size, 1):
                    time_stamp = samples[indx].timestamp
                    #print str(time_stamp) + "before"
                    dt = parser.parse(str(time_stamp))
                    print( str(dt) + "before" + "       " + dt.strftime("%s"))
                    dt = dt.astimezone(tz.tzlocal())
                    print(str(dt) + "after" + "         " + dt.strftime("%s"))
                    epoch = dt.strftime("%s")
                    print(epoch)
                    for value in values:
                        counter_id = value.id.counterId
                        meta = self.metrics_metadata[instance_key][str(counter_id)]
                        metric_id = util.get_metric(meta["name"])
                        if metric_id is None:
                            continue
                        data = _normalize_value(meta["uom"], value.value[indx])
                        util.sendMeasurement(metric_id, data, uuid, epoch)

    def _cache_metrics_metadata(self, instance_name):
        """
        Get all the performance counters metadata meaning name/group/description from the server instance
        """

        server_instance = VMWare.service_instances[instance_name]
        perf_manager = server_instance.content.perfManager

        new_metadata = {}
        for counter in perf_manager.perfCounter:
            d = dict(
                name="%s.%s.%s" % (counter.groupInfo.key, counter.nameInfo.key, counter.rollupType),
                rolluptype=counter.rollupType,
                uom=counter.unitInfo.label
            )
            new_metadata.update({str(counter.key): d})

        # Reset metadata
        self.metrics_metadata = {}
        self.metrics_metadata[instance_name] = new_metadata

    def _compute_needed_metrics(self, instance_name, available_metrics):
        """
        Compare the available metrics for one MOR we have computed and intersect them
        with the set of metrics we want to report
        """

        wanted_metrics = []
        # Get only the monitored metrics
        for metric in available_metrics:
            # No cache yet, skip it for now
            if instance_name not in self.metrics_metadata or str(metric.counterId) not in self.metrics_metadata[
                instance_name]:
                continue
            if self.metrics_metadata[instance_name][str(metric.counterId)]['name'] in self.configured_metrics:
                wanted_metrics.append(metric)
        return wanted_metrics


def _normalize_value(uom, value):
    if uom.lower() == "percent":
        value = float(value) / 100 / 100

    return value
