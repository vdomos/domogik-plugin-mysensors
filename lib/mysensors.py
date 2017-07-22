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


@author: domos  (domos p vesta at gmail p com)
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import time
import serial
from Queue import Queue


commandsType = [
        "presentation",
        "set",
        "req",
        "internal",
        "stream" 
    ]

presentationTypes = [
        "S_DOOR",
        "S_MOTION",
        "S_SMOKE",
        "S_BINARY",
        "S_DIMMER",
        "S_COVER",
        "S_TEMP",
        "S_HUM",
        "S_BARO",
        "S_WIND",
        "S_RAIN",
        "S_UV",
        "S_WEIGHT",
        "S_POWER",
        "S_HEATER",
        "S_DISTANCE",
        "S_LIGHT_LEVEL",
        "S_ARDUINO_NODE",
        "S_ARDUINO_REPEATER_NODE",
        "S_LOCK",
        "S_IR",
        "S_WATER",
        "S_AIR_QUALITY",
        "S_CUSTOM",
        "S_DUST",
        "S_SCENE_CONTROLLER",
        "S_RGB_LIGHT",
        "S_RGBW_LIGHT",
        "S_COLOR_SENSOR",
        "S_HVAC",
        "S_MULTIMETER",
        "S_SPRINKLER",
        "S_WATER_LEAK",
        "S_SOUND",
        "S_VIBRATION",
        "S_MOISTURE",
        "S_INFO",
        "S_GAS",
        "S_GPS",
        "S_WATER_QUALITY"
        ]

setreqType = [
        "V_TEMP",
        "V_HUM",
        "V_STATUS",
        "V_PERCENTAGE",
        "V_PRESSURE",
        "V_FORECAST",
        "V_RAIN",
        "V_RAINRATE",
        "V_WIND",
        "V_GUST",
        "V_DIRECTION",
        "V_UV",
        "V_WEIGHT",
        "V_DISTANCE",
        "V_IMPEDANCE",
        "V_ARMED",
        "V_TRIPPED",
        "V_WATT",
        "V_KWH",
        "V_SCENE_ON",
        "V_SCENE_OFF",
        "V_HVAC_FLOW_STATE",
        "V_HVAC_SPEED",
        "V_LIGHT_LEVEL",
        "V_VAR1",
        "V_VAR2",
        "V_VAR3",
        "V_VAR4",
        "V_VAR5",
        "V_UP",
        "V_DOWN",
        "V_STOP",
        "V_IR_SEND",
        "V_IR_RECEIVE",
        "V_FLOW",
        "V_VOLUME",
        "V_LOCK_STATUS",
        "V_LEVEL",
        "V_VOLTAGE",
        "V_CURRENT",
        "V_RGB",
        "V_RGBW",
        "V_ID",
        "V_UNIT_PREFIX",
        "V_HVAC_SETPOINT_COOL",
        "V_HVAC_SETPOINT_HEAT",
        "V_HVAC_FLOW_MODE",
        "V_TEXT",
        "V_CUSTOM",
        "V_POSITION",
        "V_IR_RECORD",
        "V_PH",
        "V_ORP",
        "V_EC",
        "V_VAR",
        "V_VA",
        "V_POWER_FACTOR"
    ]

internalType = [        
        "I_BATTERY_LEVEL",
        "I_TIME",
        "I_VERSION",
        "I_ID_REQUEST",
        "I_ID_RESPONSE",
        "I_INCLUSION_MODE",
        "I_CONFIG",
        "I_FIND_PARENT",
        "I_FIND_PARENT_RESPONSE",
        "I_LOG_MESSAGE",
        "I_CHILDREN",
        "I_SKETCH_NAME",
        "I_SKETCH_VERSION",
        "I_REBOOT",
        "I_GATEWAY_READY",
        "I_SIGNING_PRESENTATION",
        "I_NONCE_REQUEST",
        "I_NONCE_RESPONSE",
        "I_HEARTBEAT",
        "I_PRESENTATION",
        "I_DISCOVER",
        "I_DISCOVER_RESPONSE",
        "I_HEARTBEAT_RESPONSE",
        "I_LOCKED",
        "I_PING",
        "I_PONG",
        "I_REGISTRATION_REQUEST",
        "I_REGISTRATION_RESPONSE",
        "I_DEBUG"
    ]

streamType = [
        "ST_FIRMWARE_CONFIG_REQUEST",
        "ST_FIRMWARE_CONFIG_RESPONSE",
        "ST_FIRMWARE_REQUEST",
        "ST_FIRMWARE_RESPONSE",
        "ST_SOUND",
        "ST_IMAGE"
    ]



class MySensorsException(Exception):
    """
    Script exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class MySensors:
    """
    """
    # -------------------------------------------------------------------------------------------------
    def __init__(self, log, send, createdevice, stop):
        """ Init Weather object
            @param log : log instance
            @param send : callback to send values to domogik
            @param stop : Event of the plugin to handle plugin stop
            @param get_parameter : a callback to a plugin core function
        """
        self.log = log
        self.send = send
        self.createdevice = createdevice
        self.stop = stop
        self.nodes = {}

        self.msgReceiveQueue = Queue()     # http://hrb85-1-88-121-176-85.fbx.proxad.net%2Fblog%2F201606231956%2F&usg=AFQjCNHLrqciI13Np7UialO7VMDH8pxeXQ
        self.msgSendQueue = Queue()



    # -------------------------------------------------------------------------------------------------
    def gwopen(self, device):
        """ open Gateway device
        """
        self.log.info(u"==> Opening MySensors Gateway device : %s" % device)
        try:
            self.gateway = serial.Serial(device, 115200, timeout=1)
            self.log.info(u"==> Gateway opened")
            self.gateway.setDTR(True)       # DTR à '0' pour reset Arduino Nano
            resp = self.gateway.read(1024)  # Purge buffer
            time.sleep(0.2)
            self.gateway.setDTR(False)      # DTR à '0' pour reset Arduino Nano         
        except:
            error = "### Failed to open Gateway device : %s : %s" % (device, str(traceback.format_exc()))
            raise MySensorsException(error)


    # -------------------------------------------------------------------------------------------------
    def gwListen(self):
        """ listen for incoming gateway message
        """
        self.log.info(u"==> Start listening gateway ...")
        while not self.stop.isSet():
            gwline = self.gwread()
            if gwline != None:
                #self.log.info(u"==> Received : %s" % gwline.strip())
                self.msgReceiveQueue.put(gwline)                

            if not self.msgSendQueue.empty():
                 self.gwSend(self.msgSendQueue.get())
             
            time.sleep(0.2)
             
        self.log.info(u"gwListen terminated")
        self.gateway.close()
        return


    # -------------------------------------------------------------------------------------------------
    def gwread(self):
        """ read one line on gateway
        """
        
        gwReceiveLine = self.gateway.readline()
        if gwReceiveLine:
            return gwReceiveLine.decode('utf-8')
        else:
            return None
 
    
    # -------------------------------------------------------------------------------------------------
    def gwSend(self, message):
        """Write a Message to the gateway."""
        if not message:
            return
        self.gateway.write(message)    
                              

    # -------------------------------------------------------------------------------------------------
    def parseGwMsg(self):
        """
        """
        self.log.info(u"==> Start parsing gateway messages...")
        msgParts = ["nodeid", "childsensorid", "command", "ack", "type", "payload"]
        while not self.stop.isSet():
            if not self.msgReceiveQueue.empty():
                msg = self.msgReceiveQueue.get()
                try:
                    msgValue = msg.strip().split(';')
                    #self.log.info(u"==> Msg list : %s" % format(msgValue))
                except:
                    self.log.error(u"### ERROR split received msg: %s" % str(traceback.format_exc()))
                else:
                    gwMsg = dict(zip(msgParts, msgValue))
                    #self.log.info(u"==> Msg dict : %s" % format(gwMsg))
                    if commandsType[int(gwMsg["command"])] == "presentation":
                        self.processPresentationMsg(gwMsg)
                    elif commandsType[int(gwMsg["command"])] == "set" or commandsType[int(gwMsg["command"])] == "req":
                        self.processSetMsg(gwMsg)
                    elif commandsType[int(gwMsg["command"])] == "internal":
                        self.processInternalMsg(gwMsg)
                    elif commandsType[int(gwMsg["command"])] == "stream":
                        self.processStreamMsg(gwMsg)                    
                    
            time.sleep(0.2)
        self.log.info(u"parseGwMsg terminated")
        return
        

    # -------------------------------------------------------------------------------------------------
    def processPresentationMsg(self, msg):
        """
        """
        nodesensor = msg["nodeid"] + '.' + msg["childsensorid"]
        if nodesensor not in self.nodes:
            self.nodes[nodesensor] = {}
            new_nodesensor = True
        else:
            new_nodesensor = False
            
        ptype = presentationTypes[int(msg["type"])]                             # Example: "S_ARDUINO_NODE" ou "S_TEMP" 
        value = msg["payload"]                                                  # Example: "2.1.1" ou "Bureau"
        if not value: value = nodesensor                                        # If MySensors present() function called without "payload"

        if msg["childsensorid"] == "255":
            self.log.info(u"==> Receive PRESENTATION message for Node %s type=%s version='%s'" % (nodesensor, ptype, value))
            # INFO Receive PRESENTATION message for Node 46.255 type=S_ARDUINO_NODE version='2.1.1'
            if msg["nodeid"] != "0":
                if not new_nodesensor:
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodetype", ptype) 
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodeapiversion", value)
                else:
                    self.log.info(u"==> Create new Domogik 'mysensors.node' device for node '%s'" % msg["nodeid"]) 
                    self.createdevice("Node " + msg["nodeid"], nodesensor, "mysensors.node")
                    #while nodesensor not in self.nodes or not self.stop.isSet():        # Wait device creation
                    #    pass
                    self.stop.wait(2)        # Wait device creation
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodetype", ptype) 
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodeapiversion", value)

        else:
            self.log.info(u"==> Receive PRESENTATION message for Node %s type=%s Name='%s'" % (nodesensor, ptype, value))
            # INFO Receive PRESENTATION message for Node 46.2 type=S_LIGHT_LEVEL Name='Buanderie'
            if new_nodesensor:
                self.log.info(u"==> Create new Domogik 'mysensors.%s' device for sensor node '%s'" % (ptype.lower(), nodesensor)) 
                self.createdevice(value, nodesensor, "mysensors." + ptype.lower())           # "mysensors." + ptype.lower() = "mysensors.s_temp"
            else:
                ### update device ?
                pass

    
    # -------------------------------------------------------------------------------------------------
    def processSetMsg(self, msg):
        """
            Process a set message.
            44;1;1;0;1;44.8
            Node=Node44 (44), Sensor=1, command=set, ack=0, type=V_HUM  payload='44.8'
        """
        nodesensor = msg["nodeid"] + '.' + msg["childsensorid"]
        vtype = setreqType[int(msg["type"])]                        # Example: "V_HUM"
        value = msg["payload"]                                      # Example: "44.8"

        if nodesensor not in self.nodes:
            self.log.warning(u"==> New sensor node '%s' (type = '%s', value = '%s') waiting Node PRESENTATION for creating device !" % (nodesensor, vtype, value))
            return

        self.nodes[nodesensor]["vtype"] = vtype
        self.log.info(u"==> Received SET value '%s' for node '%s' (%s/%s) sensor" % (value, nodesensor, self.nodes[nodesensor]["name"], vtype.lower()))
        # INFO Received SET value '1025.9' for node '44.2' (Barometre/v_pressure) sensor
        self.send(self.nodes[nodesensor]["dmgid"], nodesensor, vtype.lower(), value)    # vtype.lower() = "v_hum"
                    


    
    # -------------------------------------------------------------------------------------------------
    def processReqMsg(self, msg):
        """Process a req message."""
        type = setreqType[int(msg["type"])]

    
    # -------------------------------------------------------------------------------------------------
    def processInternalMsg(self, msg):
        """
        """   
        nodesensor = msg["nodeid"] + '.' + msg["childsensorid"]
        itype = internalType[int(msg["type"])]                      # Example: "I_LOG_MESSAGE"
        value = msg["payload"]                                      # Example: text

        if itype == "I_LOG_MESSAGE":                                # Sent by the gateway to the Controller to trace-log a message
            self.log.debug(u"==> Received I_LOG_MESSAGE: '%s'" % value)
            return

        if itype == "I_GATEWAY_READY":                              # Send by gateway to controller when startup is complete.
            self.log.info(u"==> Received I_GATEWAY_READY information:  '%s'" % value)
            return


        if nodesensor not in self.nodes:
            self.log.warning(u"==> New sensor node '%s' (type = '%s', value = '%s') waiting Node PRESENTATION for creating device !" % (nodesensor, itype, value))
            return
        
        if itype == "I_CONFIG":                             # Config request from node. Reply with (M)etric or (I)mperal back to sensor.
            self.log.info(u"==> Received I_CONFIG request for node '%s': '%s'" % (msg["nodeid"], value))
                  
        elif itype == "I_SKETCH_NAME":                      # Optional sketch name that can be used to identify sensor in the Controller GUI
            self.log.info(u"==> Received I_SKETCH_NAME information for node '%s': '%s'" % (msg["nodeid"], value))
                  
        elif itype == "I_SKETCH_VERSION":                   # Optional sketch version that can be reported to keep track of the version of sensor in the Controller GUI
            self.log.info(u"==> Received I_SKETCH_VERSION information for node '%s': '%s'" % (msg["nodeid"], value))
                  
        elif itype == "I_BATTERY_LEVEL":                    
            self.log.info(u"==> Received I_BATTERY_LEVEL information for node '%s':  '%s'" % (msg["nodeid"], value))

        elif itype == "I_DISCOVER_RESPONSE":                 # Discover response
            self.log.info(u"==> Received I_DISCOVER_RESPONSE information (untreated) for node '%s': '%s'" % (msg["nodeid"], value))
            return
        else:
            self.log.info(u"==> Received '%s' information (untreated) for node '%s.%s':  '%s'" % (msg["nodeid"], msg["childsensorid"], itype, value))
            return

        self.send(self.nodes[nodesensor]["dmgid"], nodesensor, itype.lower(), value) 
        

    # -------------------------------------------------------------------------------------------------
    def processStreamMsg(self, msg):
        """Process a stream message."""
        stype = streamType[int(msg["type"])]
        value = msg["payload"] 
        self.log.info(u"==> Received '%s' information (untreated) for node '%s.%s':  '%s'" % (msg["nodeid"], msg["childsensorid"], stype, value))
    
    



            
            
            
