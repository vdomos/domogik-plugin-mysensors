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
import socket
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

SOCKETTIMEOUT = 360


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
    def __init__(self, log, gwdevice, send, createdevice, stop):
        """ Init Weather object
            @param log : log instance
            @param send : callback to send values to domogik
            @param stop : Event of the plugin to handle plugin stop
            @param get_parameter : a callback to a plugin core function
        """
        self.log = log
        self.gwdevice = gwdevice
        self.send = send
        self.createDevice = createdevice
        self.stop = stop
        self.nodes = {}

        self.msgReceiveQueue = Queue()     # http://hrb85-1-88-121-176-85.fbx.proxad.net%2Fblog%2F201606231956%2F&usg=AFQjCNHLrqciI13Np7UialO7VMDH8pxeXQ
        self.msgSendQueue = Queue()



    # -------------------------------------------------------------------------------------------------
    def gwopen(self, reconnect=False):
        """ open Gateway device
        """
        # For Ethernet Gateway                    
        if ":" in self.gwdevice:
            self.log.info(u"==> Open connection to MySensors Ethernet Gateway: '%s'" % self.gwdevice)
            self.ethernetGateway = True
            try:
                addr = self.gwdevice.split(':')
                addr = (addr[0], int(addr[1]))
                self.gateway = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.gateway.connect(addr)
                self.gateway.settimeout(SOCKETTIMEOUT)       # Add timeout for no blocking connection.
                self.log.info(u"==> Ethernet Gateway opened")
                return True
            except:
                if reconnect:
                    self.log.error(u"### Failed reconnecting to ethernet Gateway, Waiting few minutes before redo !" )
                    return False
                else:
                    #error = u"### Failed to open Ethernet Gateway '%s', Check if the address:port is ok" % format(self.gwdevice, traceback.format_exc())
                    error = u"### Failed to open Ethernet Gateway '%s', Check if the address:port is ok" % self.gwdevice    
                    # To test ethernet gateway: telnet @IP:5003
                    raise MySensorsException(error)

        # For Serial Gateway                    
        else:
            self.log.info(u"==> Opening connection to MySensors Serial Gateway: %s" % self.gwdevice)
            self.ethernetGateway = False
            try:
                self.gateway = serial.Serial(self.gwdevice, 115200, timeout=1)
                self.log.info(u"==> Gateway opened")
                self.gateway.setDTR(True)       # DTR set to '0' for resetting Arduino Nano
                resp = self.gateway.read(1024)  # Purge buffer
                time.sleep(0.2)
                self.gateway.setDTR(False) 
                self.log.info(u"==> Serial Gateway opened")
            except:
                error = u"### Failed to open MySensors Serial Gateway device : %s : %s" % (self.gwdevice, str(traceback.format_exc()))
                raise MySensorsException(error)


    # -------------------------------------------------------------------------------------------------
    def gwListen(self):
        """ listen for incoming gateway message
        """
        self.log.info(u"==> Start listening gateway ...")
        while not self.stop.isSet():
            
            # For Ethernet Gateway                    
            if self.ethernetGateway:
                # Receive message
                try:
                    data = self.gateway.recv(4096)
                except (socket.error, socket.timeout), e:
                    self.log.error(u"### Fail or Timeout receiving data from ethernet Gateway, Waiting few minutes before reconnect: %s" % e)
                    self.ethernetGwReconnect()
                if data:
                    for receivedMsg in data.splitlines():
                        #self.log.info(u"==> Received : %s" % receivedMsg)
                        self.msgReceiveQueue.put(receivedMsg.decode('utf-8'))

                # Send message
                if not self.msgSendQueue.empty():
                    sendMsg = self.msgSendQueue.get()
                    if sendMsg:
                        try:
                            self.gateway.send(sendMsg)
                        except socket.error, e:
                            self.log.error(u"### Failed to send message '%s' to Ethernet Gateway: '%s', Waiting few minutes before reconnect !" % (sendMsg, e))
                            self.ethernetGwReconnect()

            # For Serial Gateway                    
            else:
                # Receive message
                receivedMsg = self.gateway.readline()
                if receivedMsg:
                    self.msgReceiveQueue.put(receivedMsg.decode('utf-8'))
            
                # Send message
                if not self.msgSendQueue.empty():
                    sendMsg = self.msgSendQueue.get()
                    if sendMsg:
                        self.gateway.write(sendMsg)  
             
            time.sleep(0.2)
             
        self.log.info(u"gwListen terminated")
        self.gateway.close()
        return


    # -------------------------------------------------------------------------------------------------
    def ethernetGwReconnect(self):
        connectionok = False
        while not connectionok and not self.stop.isSet():
            self.gateway.close()
            self.stop.wait(60)
            connectionok = self.gwopen(reconnect = True)


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
            
        ptype = presentationTypes[int(msg["type"])]                             # Example: "S_ARDUINO_NODE" ou "S_TEMP" 
        value = msg["payload"]                                                  # Example: "2.1.1" ou "Bureau"
        if not value: value = nodesensor                                        # If MySensors present() function called without "payload"

        if msg["childsensorid"] == "255":
            self.log.info(u"==> Receive PRESENTATION message for Node %s type=%s version='%s'" % (nodesensor, ptype, value))
            # INFO Receive PRESENTATION message for Node 46.255 type=S_ARDUINO_NODE version='2.1.1'
            if msg["nodeid"] != "0":
                if nodesensor in self.nodes:
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodetype", ptype) 
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodeapiversion", value)
                else:
                    self.log.info(u"==> Create new Domogik 'mysensors.node' device for node '%s'" % msg["nodeid"])
                    self.createDevice("Node " + msg["nodeid"], nodesensor, "mysensors.node")
                    #while nodesensor not in self.nodes or not self.stop.isSet(): pass       # Wait device creation
                    self.stop.wait(3)        # Wait device creation
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodetype", ptype) 
                    self.send(self.nodes[nodesensor]["dmgid"], nodesensor, "nodeapiversion", value)

        else:
            self.log.info(u"==> Receive PRESENTATION message for Node %s type=%s Name='%s'" % (nodesensor, ptype, value))
            # INFO Receive PRESENTATION message for Node 46.2 type=S_LIGHT_LEVEL Name='Buanderie'
            if nodesensor not in self.nodes:
                self.log.info(u"==> Create new Domogik 'mysensors.%s' device for sensor node '%s'" % (ptype.lower(), nodesensor))
                self.createDevice(value, nodesensor, "mysensors." + ptype.lower())           # "mysensors." + ptype.lower() = "mysensors.s_temp"
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
            self.log.warning(u"==> New sensor node '%s' (type = '%s', value = '%s'), Waiting Node PRESENTATION for creating device !" % (nodesensor, vtype, value))
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
            self.log.warning(u"==> New sensor node '%s' (type = '%s', value = '%s'), Waiting Node'device to be create !" % (nodesensor, itype, value))
            return
        
        if itype == "I_CONFIG":                             # Config request from node. Reply with (M)etric or (I)mperal back to sensor.
            self.log.info(u"==> Received I_CONFIG request for node '%s': value = '%s'" % (msg["nodeid"], value))
                  
        elif itype == "I_SKETCH_NAME":                      # Optional sketch name that can be used to identify sensor in the Controller GUI
            self.log.info(u"==> Received I_SKETCH_NAME information for node '%s': value = '%s'" % (msg["nodeid"], value))
                  
        elif itype == "I_SKETCH_VERSION":                   # Optional sketch version that can be reported to keep track of the version of sensor in the Controller GUI
            self.log.info(u"==> Received I_SKETCH_VERSION information for node '%s': value = '%s'" % (msg["nodeid"], value))
                  
        elif itype == "I_BATTERY_LEVEL":                    
            self.log.info(u"==> Received I_BATTERY_LEVEL information for node '%s': value = '%s'" % (msg["nodeid"], value))

        elif itype == "I_DISCOVER_RESPONSE":                 # Discover response
            self.log.info(u"==> Received I_DISCOVER_RESPONSE information (untreated) for node '%s': value = '%s'" % (msg["nodeid"], value))
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
    
    



            
            
            
