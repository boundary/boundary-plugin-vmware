__author__ = 'Santosh Patil'
#Automatically updates mars bojects if anything is removed from VM/Added from VM

import serviceutil
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl

import atexit
import sys
import ssl
from modules import util
import collections
#ssl._create_default_https_context = ssl._create_unverified_context

def parse_propspec(propspec):
    """
    Parses property specifications.  Returns sequence of 2-tuples, each
    containing a managed object type and a list of properties applicable
    to that type

    :type propspec: collections.Sequence
    :rtype: collections.Sequence
    """

    props = []

    for objspec in propspec:
        if ':' not in objspec:
            raise Exception('property specification \'%s\' does not contain '
                            'property list' % objspec)

        objtype, objprops = objspec.split(':', 1)

        motype = getattr(vim, objtype, None)

        if motype is None:
            raise Exception('referenced type \'%s\' in property specification '
                            'does not exist,\nconsult the managed object type '
                            'reference in the vSphere API documentation' %
                            objtype)

        proplist = objprops.split(',')

        props.append((motype, proplist,))

    return props


def make_wait_options(max_wait_seconds=None, max_object_updates=None):
    waitopts = vmodl.query.PropertyCollector.WaitOptions()

    if max_object_updates is not None:
        waitopts.maxObjectUpdates = max_object_updates

    if max_wait_seconds is not None:
        waitopts.maxWaitSeconds = max_wait_seconds

    return waitopts


def make_property_collector(pc, from_node, props,self):
    """
    :type pc: pyVmomi.VmomiSupport.vmodl.query.PropertyCollector
    :type from_node: pyVmomi.VmomiSupport.ManagedObject
    :type props: collections.Sequence
    :rtype: pyVmomi.VmomiSupport.vmodl.query.PropertyCollector.Filter
    """

    # Make the filter spec
    filterSpec = vmodl.query.PropertyCollector.FilterSpec()

    # Make the object spec
    traversal = serviceutil.build_full_traversal()

    objSpec = vmodl.query.PropertyCollector.ObjectSpec(obj=from_node,
                                                       selectSet=traversal)
    objSpecs = [objSpec]

    filterSpec.objectSet = objSpecs

    # Add the property specs
    propSet = []
    for motype, proplist in props:
        propSpec = \
            vmodl.query.PropertyCollector.PropertySpec(type=motype, all=False)
        propSpec.pathSet.extend(proplist)
        propSet.append(propSpec)

    filterSpec.propSet = propSet

    try:
        pcFilter = pc.CreateFilter(filterSpec, True)
        atexit.register(pcFilter.Destroy)
        return pcFilter
    except vmodl.MethodFault, e:
        if e._wsdlName == 'InvalidProperty':
            util.sendEvent("InvalidProperty", "InvalidProperty fault while creating: [" +str(e.name )+ "]", " critical ")
            #print >> sys.stderr, "InvalidProperty fault while creating " \
            #                     "PropertyCollector filter : %s" % e.name
        else:
            util.sendEvent("Problem creating PropertyCollector", " filter : [" +str(e.faultMessage) + "]", " fault ")
            #print >> sys.stderr, "Problem creating PropertyCollector " \
             #                    "filter : %s" % str(e.faultMessage)
        raise


def monitor_property_changes(si, propspec, self,iterations=None):
    """
    :type si: pyVmomi.VmomiSupport.vim.ServiceInstance
    :type propspec: collections.Sequence
    :type iterations: int or None
    """

    pc = si.content.propertyCollector
    make_property_collector(pc, si.content.rootFolder, propspec,self)
    waitopts = make_wait_options(300)

    version = ''

    while True:
   
        result = pc.WaitForUpdatesEx(version, waitopts)

        # timeout, call again
        if result is None:
            continue
        
        # process results
        for filterSet in result.filterSet:
            for objectSet in filterSet.objectSet:
                moref = getattr(objectSet, 'obj', None)
                assert moref is not None, 'object moref should always be ' \
                                          'present in objectSet'

                moref = str(moref).strip('\'')
                kind = getattr(objectSet, 'kind', None)
                assert (
                    kind is not None and kind in ('enter', 'modify', 'leave',)
                ), 'objectSet kind must be valid'
                
                ########################New Implementaion ###############
                if kind == 'enter' or kind == 'modify' :
                    changeSet = getattr(objectSet, 'changeSet', None)
                    assert (changeSet is not None and isinstance(
                        changeSet, collections.Sequence
                    ) and len(changeSet) > 0), \
                        'enter or modify objectSet should have non-empty' \
                        ' changeSet'

                    changes = []
                    for change in changeSet:
                        name = getattr(change, 'name', None)
                        assert (name is not None), \
                            'changeset should contain property name'
                        val = getattr(change, 'val', None)
                        changes.append((name, val,))
                    virtualMachineUUID = "";
                    for n, v in changes:
                        if n=='name':
                           virtualMachineName =  v
                        elif n =='summary.config.instanceUuid':
                            virtualMachineUUID = v
                ########################END HERE Implemetaion ###########
                                    
                    if  version == '':
                        print " "
                        
                    else:
                        virtualMachineManagedObjectId = moref.split(":")
                        if virtualMachineUUID == None:
                            print "Some virtualMachineUUID comming none"
                            print virtualMachineManagedObjectId[1]
                        else:
                                if self.mors.has_key(virtualMachineUUID) == False:
                                    self.mors[virtualMachineUUID] = virtualMachineManagedObjectId[1]
                                    search_index = self.service_instance.content.searchIndex
                                    virtual_machine = search_index.FindByUuid(None, virtualMachineUUID, True, True)
                                    if virtual_machine == None :
                                      print "Values coming none"
                                    else :
                                        summary = self.service_instance.content.perfManager.QueryPerfProviderSummary(entity=virtual_machine)
                                        refresh_rate = 20
                                        if summary:
                                            if summary.refreshRate:
                                                refresh_rate = summary.refreshRate
                                                self.refresh_rates[virtualMachineUUID] = refresh_rate
                                                available_metric_ids = self.service_instance.content.perfManager.QueryAvailablePerfMetric(
                                                                                                              entity=virtual_machine)
                                                self.needed_metrics[virtualMachineUUID] = self._compute_needed_metrics(self.params['host'], available_metric_ids)
                 #Removed VM machine details      
                elif kind == 'leave': #leave
                    removeVirtualManegedObjectId = moref.split(":")
                    print removeVirtualManegedObjectId[1]
                    if  version == '':
                        print ""
                    else:
                        for key, value in self.mors.items(): # returns the dictionary as a list of value pairs -- a tuple.
                            if value == removeVirtualManegedObjectId[1]:
                                del(self.mors[key])
                        
        print "Latest mars is"
        print self.mors
        version = result.version

        if iterations is not None:
            iterations -= 1


def waitForUpdate(self):
   
    try:
        si = SmartConnect(host=self.params['host'], user=self.params['username'], pwd=self.params['password'],
                          port=int(self.params['port']))

        if not si:
            util.sendEvent("Could not connect to the specified host", " filter : [" +self.params['password'] +  self.params['username'] + "]", " critical ")
            #print >>sys.stderr, "Could not connect to the specified host ' \
             #                   'using specified username and password"
            raise

        atexit.register(Disconnect, si)
        propertiesSpecification = [];
        propertiesSpecification = ['VirtualMachine:name,summary.config.instanceUuid']
        propspec = parse_propspec(propertiesSpecification)
        #print "Monitoring property changes.  Press ^C to exit"
        monitor_property_changes(si, propspec,self, 1)

    except vmodl.MethodFault, e:
        #print >>sys.stderr, "Caught vmodl fault :\n%s" % str(e)
        util.sendEvent("Plugin vmware:", " Caught vmodl fault : [" + str(e) + "]", " fault ")
        raise
    except Exception, e:
        #print >>sys.stderr, "Caught exception : " + str(e)
        util.sendEvent("Plugin vmware:", " Caught exception : [" + str(e) + "]", " exception ")
        raise

