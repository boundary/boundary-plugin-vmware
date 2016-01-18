__author__ = 'gokumar'

"""
DataCollector that collects the VMs' details/performance metrics from vCenter
"""

import atexit
from dateutil import parser
import sys
import datetime
from requests.packages import urllib3
from requests.exceptions import ConnectionError
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

from modules import util
from modules import  waitforupdates

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

    def __init__(self, config):
        """
        Initialization is responsible for fetching service instance objects for each vCenter instance
        pyvmomi has some security checks enabled by default from python 2.7.9 onward to connect to vCenter.
        """

        # Holds all the VMs' instanceuuid that are discovered for each of the vCenter. Going ahead it would hold all the
        # other managed objects of vCenter that would be monitored.
        self.mors = {}

        self.params = config

        global metrics
        global counters

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
        
        # Disabling the security warning message, as the certificate verification is disabled
        urllib3.disable_warnings()

        try:
            service_instance = connect.SmartConnect(host=self.params['host'],
                                                    user=self.params['username'],
                                                    pwd=self.params['password'],
                                                    port=int(self.params['port']))
            atexit.register(connect.Disconnect, service_instance)
            self.service_instance = service_instance
            self._cache_metrics_metadata(self.params['host'])
        except KeyError as ke:
            util.sendEvent("Plugin vmware: Key Error", "Improper param.json, key missing: [" + str(ke) + "]", "error")
            sys.exit(-1)
        except ConnectionError as ce:
            util.sendEvent("Plugin vmware: Error connecting to vCenter", "Could not connect to the specified vCenter host: [" + str(ce) + "]", "critical")
            sys.exit(-1)
        except StandardError as se:
            util.sendEvent("Plugin vmware: Unknown Error", "[" + str(se) + "]", "critical")
            sys.exit(-1)
        except vim.fault.InvalidLogin as il:
            util.sendEvent("Plugin vmware: Error logging into vCenter", "Could not login to the specified vCenter host: [" + str(il) + "]", "critical")
            sys.exit(-1)

    def discovery(self):
        """
        This method is responsible to discover all the entities that belongs to all the vCenter instances that are
        configured
        """

        content = self.service_instance.RetrieveContent()
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
                self.create_vms(self.params['host'], virtual_machine, self.params['maxdepth'])

	    #calling wait for update method to handle add or remove vms from list based on VM unique values
            waitforupdates.waitForUpdate(self)

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
            #uuid = virtual_machine.config.instanceUuid
	    uuid = virtual_machine._moId #It will give unique id of vcenter level of vms
            name = virtual_machine.config.name

            if vcenter_name not in self.mors:
                self.mors[vcenter_name] = []

            if uuid not in self.mors[vcenter_name]:
                self.mors[vcenter_name].append(uuid)
                summary = self.service_instance.content.perfManager.QueryPerfProviderSummary(entity=virtual_machine)
                refresh_rate = 20
                if summary:
                    if summary.refreshRate:
                        refresh_rate = summary.refreshRate

                self.refresh_rates[uuid] = refresh_rate

                available_metric_ids = self.service_instance.content.perfManager.QueryAvailablePerfMetric(
                    entity=virtual_machine)

                self.needed_metrics[uuid] = self._compute_needed_metrics(vcenter_name, available_metric_ids)

    def collect(self):
        """
        This method is responsible to traverse through the mors[] and query metrics for each of the managed object that
        is discovered for all the vCenters.
        """

        instance_key = self.params['host']
        content = self.service_instance.RetrieveContent()
        search_index = self.service_instance.content.searchIndex

        polling_interval = self.params['pollInterval']
        max_samples = self.params['maxSamples']

        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(seconds=polling_interval / 1000)

        try:
            if instance_key in self.mors:
                for uuid in self.mors[instance_key]:
                    vm = search_index.FindByUuid(None, uuid, True, True)
                    if vm is not None:
                        if uuid in self.needed_metrics:
                            needed_metric_ids = self.needed_metrics[uuid]
                            if uuid in self.refresh_rates:
                                refresh_rate = self.refresh_rates[uuid]

                                query = vim.PerformanceManager.QuerySpec(intervalId=refresh_rate,
                                                                         maxSample=max_samples,
                                                                         entity=vm,
                                                                         metricId=needed_metric_ids,
                                                                         startTime=start_time,
                                                                         endTime=end_time)
                                result = content.perfManager.QueryPerf(querySpec=[query])
                                self._parse_result_and_publish(instance_key, vm.config.name, result, self.params['host'], self.params['app_id'])
                            else:
                                util.sendEvent("Plugin vmware: Refresh Rate unavailable", "Refresh rate unavailable for a vm, ignoring", "warning")
                        else:
                            util.sendEvent("Plugin vmware: Needed metrics unavailable", "Needed metrics unavailable for a vm, ignoring", "warning")

        except vmodl.MethodFault as error:
            util.sendEvent("Error", str(error), "error")

    def _parse_result_and_publish(self, instance_key, uuid, result, vcenter_name, app_id):
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
                    dt = parser.parse(str(time_stamp))
                    dt = dt.replace(tzinfo=None)
                    epoch = str(util.unix_time_millis(dt))
                    for value in values:
                        counter_id = value.id.counterId
                        meta = self.metrics_metadata[instance_key][str(counter_id)]
                        metric_id = util.get_metric(meta["name"])
                        if metric_id is None:
                            continue
                        data = _normalize_value(meta["uom"], value.value[indx])
                        util.sendMeasurement(metric_id, data, uuid, epoch, app_id, 'vm', vcenter_name, 'vcenter')

    def _cache_metrics_metadata(self, instance_name):
        """
        Get all the performance counters metadata meaning name/group/description from the server instance
        """

        perf_manager = self.service_instance.content.perfManager

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
    elif uom.lower() == "kb":
        value = float(value) * 1024
    elif uom.lower() == "kbps":
	value = float(value) * 1024
    return value
