"""
<plugin key="DLBOARD" name="DL Board plugin - SERIAL" author="Luca Subiaco e Daniele Gava" version="1.0.0" externallink="https://www.dmocontrol.info/" wikilink="https://www.domocontrol.info">
	<params>
         <param field="Mode6" label="Debug" width="125px">
            <options>
                <option label="None" value="0"  default="true"/>
                <option label="Verbose" value="2"/>
                <option label="Domoticz Framework - Basic" value="62"/>
                <option label="Domoticz Framework - Basic+Messages" value="126"/>
                <option label="Domoticz Framework - Connections Only" value="16"/>
                <option label="Domoticz Framework - Connections+Queue" value="144"/>
                <option label="Domoticz Framework - All" value="-1"/>
            </options>
        </param>
	</params>
</plugin>
"""

"""
"Air Quality"
"Alert"
"Barometer"
"Counter Incremental"
"Current/Ampere"7
"Current (Single)"
"Custom"
"Distance"
"Gas"
"Humidity"
"Illumination"
"kWh"
"Leaf Wetness"
"Percentage"
"Pressure"
"Rain"
"Selector Switch"
"Soil Moisture"
"Solar Radiation"
"Sound Level"
"Switch"
"Temperature"
"Temp+Hum"
"Temp+Hum+Baro"
"Text"
"Usage"
"UV"
"Visibility"
"Voltage"
"Waterflow"
"Wind"
"Wind+Temp+Chill"
"""

import Domoticz
import time
import sys
from pprint import pprint
import json
from dl485 import Bus, Log

print("-" * 50, "Begin DL485-Serial plugin", "-" * 50, end="\n")
config_file_name = "/home/pi/domoticz/plugins/DL485_DOMOTICZ/config.json"  # File di configurazione
logstate = 1
b = Bus(config_file_name, logstate)  # Istanza la classe Bus
# log = Log()  # Istanza la classe Log
DevicesCreate = {} # DICT con tutti i dispositivi DL485 creati 
# Configurazione SCHEDE
# msg = b.resetEE(1, 0)  # Board_id, logic_io. Se logic_io=0, resetta tutti gli IO
# print(msg)
# b.TXmsg += msg
# b.dictBoardIo()  # Crea il DICT con i valori IO basato sul file di configurazione (solo board attive)

"""
Image:
0 = Light bulb
1 = Shuko socket
2 = Monitor LCD
3 = Hard Disk
4 = Printer
5 = Audio amplifier
6 = Notebook
7 = Fan
8 = Speaker
9 = Input pushbutton
10 = Fireplace
11 = Water
15 = Manometro
24 = Printer

"""


""" LOOP """
class BasePlugin:
    def __init__(self):
        self.debug = 0
        self.mapUnit2DeviceID = {}
        configuration = b.getConfiguration()  # Set configuration of boards
        b.TXmsg = configuration # Mette trama configurazione in lista da inviare
        self.devices = {
            'Unit2DeviceID': {},
            'DeviceID2Unit': {},
        } # DICT with all devices

    def unitPresent(self, listUnit):
        """
        Ritorna il numero più piccolo non presente sulla lista diveso da zero
        """
        listUnit.sort()
        n = 1
        for x in listUnit:
            if n in listUnit: # Numero presente nella lista
                pass
            else: # Numero non presente nella lista
                return n
            n += 1
        return n

    def onStart(self):
        self.debug = int(Parameters["Mode6"])
        
        Domoticz.Log("Start DL485 Loop Plugin with Debug: %s" %self.debug)       
        """
        0 	None. All Python and framework debugging is disabled.
        1 	All. Very verbose log from plugin framework and plugin debug messages.
        2 	Mask value. Shows messages from Plugin Domoticz.Debug() calls only.
        4 	Mask Value. Shows high level framework messages only about major the plugin.
        8 	Mask Value. Shows plugin framework debug messages related to Devices objects.
        16 	Mask Value. Shows plugin framework debug messages related to Connections objects.
        32 	Mask Value. Shows plugin framework debug messages related to Images objects.
        64 	Mask Value. Dumps contents of inbound and outbound data from Connection objects.
        128 	Mask Value. Shows plugin framework debug messages related to the message queue.
        """
        Domoticz.Debugging(self.debug)
        
        for d in Devices:
            print(Devices[d])
            self.devices['Unit2DeviceID'][Devices[d].Unit] = Devices[d].DeviceID
            self.devices['DeviceID2Unit'][Devices[d].DeviceID] = Devices[d].Unit
        # print(self.devices)
        
        for board_id in b.mapiotype:
            for logic_io in b.mapiotype[board_id]:
                board_enable = b.mapiotype[board_id][logic_io]['board_enable']
                io_enable = b.mapiotype[board_id][logic_io]['enable']
                device_enable = board_enable & io_enable             
                device_type = b.mapiotype[board_id][logic_io]['device_type']    
                print(device_type)
                if device_type in ['DIGITAL_IN_PULLUP', 'DIGITAL_IN']:
                    image = 9
                elif device_type in ['DIGITAL_OUT']:
                    image = 0
                else:
                    image = 0
                
                DeviceID = "%s-%s" % (board_id, logic_io)
                
                name = "[%s] %s" % (DeviceID, b.mapiotype[board_id][logic_io]['name'])
                description = b.mapiotype[board_id][logic_io]['description']
                dtype = b.mapiotype[board_id][logic_io]['dtype']
                
                # print("*** BID:{} IOID:{} - logic_io:{} Board_enable:{} - Domoticz Device ENABLE:{} - DeviceID:{}".format(board_id, board_enable, logic_io, io_enable, device_enable, DeviceID))

                if DeviceID not in self.devices['DeviceID2Unit'].keys():
                    unit_present = list(self.devices['Unit2DeviceID'].keys())
                    Unit = self.unitPresent(unit_present)
                    Domoticz.Device(Name=name, Unit=Unit, TypeName=dtype, Description=description, DeviceID=DeviceID, Image=image).Create()
                    self.devices['Unit2DeviceID'][Unit] = DeviceID
                    self.devices['DeviceID2Unit'][DeviceID] = Unit

                value = int(b.mapiotype[board_id][logic_io]['default_startup_value']) if 'default_startup_value' in b.mapiotype[board_id][logic_io] else 0
                sValue = 'On' if value else 'Off'

                if dtype == 'switch':
                    pass
                elif dtype == 'Temp+Hum':
                    sValue = "0;0;0"
                elif dtype == 'Temp+Hum+Baro':
                    sValue = "0;0;0;0;0"

                Unit = self.devices['DeviceID2Unit'][DeviceID]

                Devices[Unit].Update(Name=name, TypeName=dtype, Description=description, nValue=value, sValue=sValue, Used=1)

        # self.SerialConn = Domoticz.Connection(Name="DL485", Transport="Serial", Address = Parameters["SerialPort"], Baud = int(Parameters["Mode3"]))
        self.SerialConn = Domoticz.Connection(Name="DL485", Transport="Serial", Address=b.bus_port, Baud=b.bus_baudrate)
        self.SerialConn.Connect()

    def onStop(self):
        Domoticz.Log("%s %s" % ("onStop DL485-SERIAL plugin", self))

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("%s %s %s %s %s" % ("onConnect DL485-SERIAL plugin", self, Connection, Status, Description))

    def onCommand(self, Unit, Command, Level, Hue):
        # print("onCommand", Unit, Command, Level, Hue)
        bio = Devices[Unit].DeviceID.split("-")
        board_id = int(bio[0])
        logic_io = int(bio[1])
        value = 1 if Command == 'On' else 0
        msg = b.writeIO(board_id, logic_io, [value])
        b.TXmsg.append(msg)

    def updateIO(self, board_id, logic_io, value):
        """
        Viene chiamata quando arriva una trama dalla rete per poter decodificare il messaggio e aggiornare lo stato di Domoticz
        """
        # print("updateIO", board_id, logic_io, value)
        if not board_id in b.mapiotype or not logic_io in b.mapiotype[board_id]:
            print("updateIO -> Board ID %s o IoLogic %s non trovati sul file di configurazione" %(board_id, logic_io) )
            return

        DeviceID = '%s-%s' %(board_id, logic_io)
        
        if not DeviceID in self.devices['DeviceID2Unit']: 
            # pprint(self.devices)
            print("CHIAVE NON TROVATA SUL DICT IO di DOMOTICZ:", DeviceID)    
            return

        Unit = self.devices['DeviceID2Unit'][DeviceID]
        dtype = b.mapiotype[board_id][logic_io]['dtype']
        
        # print("==>>dtype: {:<15} board_id: {:<5} logic_io: {:<5} value: {}".format(dtype, board_id, logic_io, value))

        if (Unit in Devices):
            # Domoticz.Debug("Device:{}, Board_id:{}, logic_io:{}, value:{}".format(dtype, board_id, logic_io, value))
            if dtype == 'Switch':
                # b0: dato filtrato
                # b1: dato istantaneo
                # b2: fronte OFF
                # b3: fronte ON
                # b4: fronte OFF da trasmettere
                # b5: fronte ON da trasmettere

                # x_value = value[0]
                # value = value[0]
                # value = b.make_inverted(board_id, logic_io, value[0] & 1)  # Inverte l'IO se definito sul file di configurazione
                # b.status[board_id]['io'][logic_io - 1] = value

                
                sValue = 'On' if value & 1 == 1 else 'Off'
                
                Devices[Unit].Update(nValue=value&1, sValue=sValue)
                
                linked_proc = b.mapproc[DeviceID] if DeviceID in b.mapproc else {}
                
                plc_function = b.mapiotype[board_id][logic_io]['plc_function']

                if linked_proc and plc_function == 'disable' and 1==2: # Da rifare perché non FUNZIONA
                    """
                        elenco linked proc
                        toggle
                        direct (accetta un solo ingresso e lo replica direttamente)
                        invert (accetta un solo ingresso e lo replica invertito)
                        and (n ingressi in and)
                        or
                        xor
                        nand
                        nor
                        nxor
                    """

                    for x_out in linked_proc:
                        x_outa = x_out.split("-")
                        x_board_id = int(x_outa[0])
                        x_logic_io = int(x_outa[1])

                        app_linked_proc = linked_proc["%s-%s" %(x_outa[0], x_outa[1])]['linked_proc']
                        
                        if app_linked_proc == 'toggle':
                            if x_value & 0b100:
                                value = b.status[x_board_id]['io'][x_logic_io - 1]
                                value = 1 - value

                                value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                                # print("TOGGLE", x_out, value)
                                msg = b.writeIO(x_board_id, x_logic_io, [value])
                                b.TXmsg.append(msg)

                        elif app_linked_proc == 'direct':
                            value = x_value & 1
                            value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                            # print("DIRECT", x_out, value)
                            msg = b.writeIO(x_board_id, x_logic_io, [value])
                            b.TXmsg.append(msg)

                        elif app_linked_proc == 'invert':
                            value = (x_value & 1) ^ 1
                            value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                            # print("INVERT", x_out, value)
                            msg = b.writeIO(x_board_id, x_logic_io, [value])
                            b.TXmsg.append(msg)
                        elif app_linked_proc == 'and':
                            linked_board_id_logic_io = b.mapiotype[x_board_id][x_logic_io]['linked_board_id_logic_io']
                            # print("linked_board_id_logic_io", linked_board_id_logic_io)
                            value = 1
                            for ii in linked_board_id_logic_io:
                                ii_outa = ii.split("-")
                                ii_board_id = int(ii_outa[0])
                                ii_logic_io = int(ii_outa[1])
                                value = value & b.status[ii_board_id]['io'][ii_logic_io - 1]
                            value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                            msg = b.writeIO(x_board_id, x_logic_io, [value])
                            b.TXmsg.append(msg)

                        elif app_linked_proc == 'or':
                            linked_board_id_logic_io = b.mapiotype[x_board_id][x_logic_io]['linked_board_id_logic_io']
                            value = 0
                            for ii in linked_board_id_logic_io:
                                ii_outa = ii.split("-")
                                ii_board_id = int(ii_outa[0])
                                ii_logic_io = int(ii_outa[1])
                                value = value | b.status[ii_board_id]['io'][ii_logic_io - 1]
                            value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                            msg = b.writeIO(x_board_id, x_logic_io, [value])
                            b.TXmsg.append(msg)
                        elif app_linked_proc == 'xor':
                            linked_board_id_logic_io = b.mapiotype[x_board_id][x_logic_io]['linked_board_id_logic_io']
                            value = 0
                            for ii in linked_board_id_logic_io:
                                ii_outa = ii.split("-")
                                ii_board_id = int(ii_outa[0])
                                ii_logic_io = int(ii_outa[1])
                                value = value ^ b.status[ii_board_id]['io'][ii_logic_io - 1]
                            value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                            msg = b.writeIO(x_board_id, x_logic_io, [value])
                            b.TXmsg.append(msg)

            elif dtype == 'Voltage':
                sValue = str(value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = int(value), sValue = sValue)
                Domoticz.Debug("Device:{}, Board_id:{}, logic_io:{}, value:{}".format(dtype, board_id, logic_io, value))

            elif dtype == 'Temperature':
                if value:
                    sValue = str(value)
                    bio = '%s-%s' %(board_id, logic_io)
                    if bio in b.mapproc:
                        # print("DS18B20 LINKED BOARD", bio, b.mapproc[bio])
                        board_id_linked = b.mapproc[bio]["board_id"]
                        logic_io_linked = b.mapproc[bio]["logic_io"]
                        # print(board_id_linked, logic_io_linked)
                        device_type_linked = b.mapiotype[board_id_linked][logic_io_linked]['device_type']
                        if device_type_linked =="PSYCHROMETER":
                            # print(device_type_linked)
                            
                            value_humidity = b.status[board_id_linked]['io'][logic_io_linked - 1]
                            if value_humidity:
                                print("PSYCHROMETER",value_humidity,  board_id_linked, logic_io_linked)
                                DeviceIDLinked = '%s-%s' %(board_id_linked, logic_io_linked)
                                if not DeviceIDLinked in self.mapUnit2DeviceID: return

                                UnitLinked = self.mapUnit2DeviceID[DeviceIDLinked]
                                dtypeLinked = b.mapiotype[board_id_linked][logic_io_linked]['dtype']
                                if value_humidity < 40:
                                    hum_status = 2
                                elif value_humidity >=45 and value_humidity < 56:
                                    hum_status = 1
                                elif value_humidity >=60:                                    
                                    hum_status = 3
                                else:
                                    hum_status = 0

                                # print(UnitLinked, dtypeLinked)
                                Devices[UnitLinked].Update(nValue = int(value_humidity), sValue = '%s' %hum_status)

                    b.status[board_id]['io'][logic_io - 1] = value
                    Devices[Unit].Update(nValue = 0, sValue = sValue)
                    Domoticz.Debug("Device:{}, Board_id:{}, logic_io:{}, value:{}".format(dtype, board_id, logic_io, value))

            elif dtype == 'Temp+Hum+Baro':
                hum_stat = 0
                if value[1] >= 70: hum_stat = 3
                elif value[1] <= 30: hum_stat = 2
                elif value[1] > 30 and value[1] <= 45: hum_stat = 0
                elif value[1] > 45 and value[1] < 70: hum_stat = 1

                # Barometer forecast
                # <1000: rain, <1020: Cloudy, <1030: Partially Cloudy; >=1030: sunny
                # 0 = No info, 1 = Sunny, 2 = Partly cloudy, 3 = Cloudy, 4 = Rain

                weather_prediction = 0
                if value[2] < 1000: weather_prediction = 4
                elif value[2] < 1020: weather_prediction = 3
                elif value[2] < 1030: weather_prediction = 2
                else: weather_prediction = 1

                sValue = "{};{};{};{};{}".format(value[0], value[1], hum_stat, value[2], weather_prediction)
                # print("Unit in devices", dtype, Unit, sValue)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue=0, sValue=sValue)
                Domoticz.Debug("Device:{}, Board_id:{}, logic_io:{}, value:{}".format(dtype, board_id, logic_io, value))
                
            elif dtype == 'Temp+Hum':
                # value = b.calculate(board_id, logic_io, value)
                # print("TEMPERATURA AM2320", board_id, logic_io, value)

                # ranges from about 70% wet, below 30 Dry, between 30 and 45 Normal, and 45 and 70 comfortable
                #  0=Normal, 1=Comfortable, 2=Dry, 3=Wet
                hum_stat = 0
                if value[1] >= 70: hum_stat = 3
                elif value[1] <= 30: hum_stat = 2
                elif value[1] > 30 and value[1] <= 45: hum_stat = 0
                elif value[1] > 45 and value[1] < 70: hum_stat = 1

                # Barometer forecast
                # <1000: rain, <1020: Cloudy, <1030: Partially Cloudy; >=1030: sunny
                # 0 = No info, 1 = Sunny, 2 = Partly cloudy, 3 = Cloudy, 4 = Rain

                weather_prediction = 0
                # if value[2] < 1000: weather_prediction = 4
                # elif value[2] < 1020: weather_prediction = 3
                # elif value[2] < 1030: weather_prediction = 2
                # else: weather_prediction = 1

                sValue = "{};{};{}".format(value[0], value[1], hum_stat)
                # print("Unit in devices", dtype, Unit, sValue)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue=0, sValue=sValue)
                Domoticz.Debug("Device:{}, Board_id:{}, logic_io:{}, value:{}".format(dtype, board_id, logic_io, value))
            
            elif dtype == 'Counter Incremental':
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = value&1, sValue = str(value&1))
                Domoticz.Debug("Device:{}, Board_id:{}, logic_io:{}, value:{}".format(dtype, board_id, logic_io, value))
            
            elif dtype == "kWh":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                # str(en_0)+";"+str(en_1 * 1000)
                Devices[Unit].Update(nValue = 0, sValue = "%s;%s" %(value, 0)) 
                
            elif dtype == "Counter":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = value, sValue = str(value))     

            elif dtype == "Custom Sensor":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = int(value), sValue = str(value)) 

    def onMessage(self, Connection, RXbytes):
        for d in RXbytes:
            b.RXtrama = b.readSerial(d)
            
            if not b.RXtrama: 
                continue
            
            b.arrivatatrama()
                        
            # print(b.RXtrama) # Non togliere altrimenti non funziona
            if len(b.RXtrama) > 1:  # Mosra solo comunicazioni valide (senza PING)
                print("Trama arrivata:", b.RXtrama, b.int2hex(b.RXtrama))
                # if (b.RXtrama[1] & 0xDF) in b.code: # comando valido o feedback a comando valido
                
                if b.RXtrama[1] & 0xDF == b.code['COMUNICA_IO']:  # COMUNICA_IO / Scrive valore USCITA
                    # print("onMessage>>>", b.RXtrama)
                    
                    value = b.calculate(b.RXtrama[0], b.RXtrama[2], b.RXtrama[3:])  # Aggiorna DOMOTICZ
                    self.updateIO(b.RXtrama[0], b.RXtrama[2], value)  # Aggiorna DOMOTICZ
                        
                    # print("VALUE CALCULATE:", b.RXtrama[0], b.RXtrama[2], b.RXtrama[3:], value)

                
            b.writeLog()

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        pass

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")
        Domoticz.Log("Plugin DL485 Disconnected")

    def onHeartbeat(self):
        return 1


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != str(sValue)):
            Devices[Unit].Update(nValue, str(sValue))
    return


# Generic helper functions
def DumpConfigToLog():
    # for x in Parameters:
    #     if Parameters[x] != "":
    #         Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    # Domoticz.Debug("Device count: " + str(len(Devices)))
    # for x in Devices:
    #     Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
    #     Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
    #     Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
    #     Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
    #     Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
    #     Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
