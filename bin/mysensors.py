#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

MySensors

Implements
==========

- MySensorsManager

"""

import zmq
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from domogik.common.plugin import Plugin
from domogik.common.utils import get_sanitized_hostname

from domogik_packages.plugin_mysensors.lib.mysensors import MySensors, MySensorsException
import threading
import traceback
import json

class MySensorsManager(Plugin):
    """ 
    """

    # -------------------------------------------------------------------------------------------------
    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='mysensors')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return

        # get the devices list
        self.devices = self.get_device_list(quit_if_no_device = False)

        # get the sensors id per device : 
        self.sensors = self.get_sensors(self.devices)

        self.mysensors_gwdevice = self.get_config("gw_device")
        self.mysensors_autocreatedev = self.get_config("autocreatedev")
        
        # Init MySensors Manager
        self.mysensorsmanager = MySensors(self.log, self.send_data, self.mysensors_autocreatedev, self.create_device, self.add_detected_device, self.get_stop())
        
        # Set nodes list
        self.setMySensorsNodesList(self.devices)

        # Open the MySensors serial device
        try:
            self.mysensorsmanager.gwopen(self.mysensors_gwdevice)
        except MySensorsException as e:
            self.log.error(e.value)
            print(e.value)
            self.force_leave()
            return
            
        self.log.info(u"==> Launch 'gwListen' thread") 
        thr_name = "thr_gwListen"
        self.thread_gwListen = threading.Thread(None,
                                          self.mysensorsmanager.gwListen,
                                          thr_name,
                                          (),
                                          {})
        self.thread_gwListen.start()
        self.register_thread(self.thread_gwListen)

        self.log.info(u"==> Launch 'parseGwMsg' thread") 
        thr_name = "thr_parseGwMsg"
        self.thread_parseGwMsg = threading.Thread(None,
                                          self.mysensorsmanager.parseGwMsg,
                                          thr_name,
                                          (),
                                          {})
        self.thread_parseGwMsg.start()
        self.register_thread(self.thread_parseGwMsg)

        self.log.info(u"==> Add callback for new or changed devices.")
        self.register_cb_update_devices(self.reload_devices)
        
        self.ready()


    # -------------------------------------------------------------------------------------------------
    def setMySensorsNodesList(self, devices):
        self.log.info(u"==> Set MySensors nodes devices list ...")
  
        for a_device in devices:    # For each device
            # self.log.info(u"==> a_device:   %s" % format(a_device))
            device_id = a_device["id"]                                          # Ex.: "73"
            device_name = a_device["name"]                                      # sname Ex.: Name send in Present() function of Node sketch
                       
            nodesensor = self.get_parameter(a_device, "nodesensor")             # Parameter nodesensor => "44.0"
            if nodesensor and self.is_number(nodesensor) and "." in nodesensor:
                self.mysensorsmanager.nodes.update({nodesensor : {"name": device_name, "dmgid": device_id, "vtype": ""}})       
                # {"44.0": {"name": "Bureau", "dmgid": "120"}} or {"44.255": {"name": "Node 44", "dmgid": "100"}} 
                self.log.info(u"==> Device Node.Sensor '%s' : '%s'" % (nodesensor, format(self.mysensorsmanager.nodes[nodesensor])))
            else:
                self.log.error(u"### Node.id parameter '%s' malformated or empty" % nodesensor)
                continue
            
                        
 
    # -------------------------------------------------------------------------------------------------
    def send_data(self, device_id, nodesensor, sensordevice, value):
        """ Send the mysensors sensors values over MQ
        """
        data = {}
        devicename = self.mysensorsmanager.nodes[nodesensor]["name"]
        data[self.sensors[device_id][sensordevice]] = value         # sensordevice = "v_temp" or i_battery_level or "nodetype", ...                         
        self.log.info("==> Publish value '%s' for node '%s' (%s/%s) sensor" % (value, nodesensor, devicename, sensordevice))

        try:
            self._pub.send_event('client.sensor', data)
        except:
            self.log.error(u"### Bad MQ message to send : {0}".format(data))
            pass


    # -------------------------------------------------------------------------------------------------
    def on_mdp_request(self, msg):
        """ Called when a MQ req/rep message is received
        """
        ### NON TESTE !
        
        Plugin.on_mdp_request(self, msg)
        #self.log.info(u"==> Received MQ message: %s" % format(msg))
        # => MQ Request received : <MQMessage(action=client.cmd, data='{u'state': u'1', u'command_id': 14, u'device_id': 39}')>
    
        if msg.get_action() == "client.cmd":
            data = msg.get_data()
            #self.log.debug(u"==> Received MQ REQ command message: %s" % format(data))      
            # DEBUG ==> Received MQ REQ command message: {u'value': u'1', u'command_id': 50, u'device_id': 139}
            device_id = data["device_id"]
            command_id = data["command_id"]
                        
            # {"44.0": {"name": "Bureau", "dmgid": "120", "vtype": "V_STATUS"}}
            for node in self.mysensorsmanager.nodes:
                if '255' not in node:
                    if nodes[node]['dmgid'] == device_id: 
                        nodesensor_name = nodes[node]['name']            # "Relay #1"
                        nodesensor_vtype = nodes[node]['vtype']          # "V_STATUS"
                        break
            if nodesensor_vtype in ["V_STATUS", "V_UP", "V_DOWN", "V_STOP", "V_PERCENTAGE", "V_IR_SEND"]:
                msg = node.replace(".",";") + '1;0;' + self.mysensorsmanager.setreqType.index(nodesensor_vtype) + ";" + data["value"]  + "\n"
                # msg = "42;0;1;0;2;1\n"      nodeid;childsensorid;set command;no ack;vtype;value\n
                # Command from the controller (1 = SET), Outgoing message to node 42 child sensor 0, Set V_STATUS (2) variable to 1 (turn on). No ack is requested from destination node.
                self.log.info(u"==> Send SET message '%s' for device '%s/%s' (id:%s) to Gateway" % (msg, nodesensor_name, nodesensor_vtype.lower(), device_id))
                self.mysensorsmanager.msgSendQueue.put(msg)
      
                # Reply MQ REP (acq) to REQ command
                self.send_rep_ack(True, None, command_id, device_name) ;
            else: 
                self.log.error(u"### Node sensor vtype not found for device '%s' (id:%s)" % (nodesensor_name, device_id))


    # -------------------------------------------------------------------------------------------------
    def send_rep_ack(self, status, reason, cmd_id, dev_name):
        """ Send MQ REP (acq) to command
        """
        self.log.info(u"==> Reply MQ REP (acq) to REQ command id '%s' for device '%s'" % (cmd_id, dev_name))
        reply_msg = MQMessage()
        reply_msg.set_action('client.cmd.result')
        reply_msg.add_data('status', status)
        reply_msg.add_data('reason', reason)
        self.reply(reply_msg.get())


    # -------------------------------------------------------------------------------------------------
    def reload_devices(self, devices):
        """ Called when some devices are added/deleted/updated
        """
        self.log.info(u"==> Reload Device called")
        self.setMySensorsNodesList(devices)
        self.devices = devices
        self.sensors = self.get_sensors(devices)

        
    # -------------------------------------------------------------------------------------------------
    def create_device(self, name, nodeidchildid, devicetype):
        """ Create a new device for this plugin
        """
        client_id  = "plugin-mysensors.{0}".format(get_sanitized_hostname())
        # name = "Node xx" or SensorName/Node_id.Child_id
        # nodeidchildid = Node_id.Child_id
        # devicetype = "mysensors.node" or "mysensors.s_temp" ...
        devicedata = {'data':
            {
                u'name': name,                  
                u'description': "",
                u'reference': "",
                u'global': [
                    {
                        u'key': u'nodesensor',
                        u'value': nodeidchildid,
                        u'type': u'string',
                        u'description': u'nodeid.sensorid'
                    }
                ],
                u'client_id': client_id,
                u'device_type': devicetype,
                u'xpl': [],
                u'xpl_commands': {},
                u'xpl_stats': {}
            }
        }

        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.create')
        msg.set_data(devicedata)
        response = cli.request('dbmgr', msg.get(), timeout=10).get()
        create_result = json.loads(response[1])             # response[1] is a string !
        self.log.debug(u"==> Create device result: '%s'" % response)
        if not create_result["status"]:
            self.log.error("### Failed to create device '%s' (%s) !" % (nodeidchildid))


    # -------------------------------------------------------------------------------------------------
    def add_detected_device(self, name, nodeidchildid, devicetype):
        ''' Add new detected device
        @param name : Device's name
        @param nodeidchildid : Node id
        @param devicetype : Devices's type
        '''
        self.device_detected({
            "device_type" : devicetype,
            "name": name,
            "reference" : "Node " + nodeidchildid,
            "global" : [{"key": "nodesensor", "value": nodeidchildid}],
            "xpl" : [],
            "xpl_commands" : {},
            "xpl_stats" : {}
        })

    # -------------------------------------------------------------------------------------------------
    def is_number(self, s):
        ''' Return 'True' if s is a number
        '''
        try:
            float(s)
            return True
        except ValueError:
            return False
        except TypeError:
            return False


if __name__ == "__main__":
    mysensors = MySensorsManager()
