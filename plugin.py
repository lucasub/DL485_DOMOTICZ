"""
<plugin key="DL485_V1" name="DL Board plugin V1 - SERIAL" author="Luca Subiaco e Daniele Gava" version="1.3" externallink="https://www.dmocontrol.info/" wikilink="https://www.domocontrol.info">
	<params>
         <param field="Mode6" label="Debug" width="125px">
            <options>
                <option label="None" value="0"  default="true"/>
                <option label="Very verbose" value="1"/>
                <option label="Shows messages from Plugin" value="2"/>
                <option label="Shows high level framework messages only about major the plugin" value="4"/>
                <option label="Shows plugin framework debug messages related to Devices objects" value="8"/>
                <option label="Shows plugin framework debug messages related to Connections objects" value="16"/>
                <option label="Shows plugin framework debug messages related to Images objects" value="32"/>
                <option label="Dumps contents of inbound and outbound data from Connection objects" value="64"/>
                <option label="Shows plugin framework debug messages related to the message queue" value="128"/>
            </options>
        </param>
	</params>
</plugin>
"""

import Domoticz
import time
import sys
from pprint import pprint
import json
from dl485 import Bus, Log

print("-" * 50, "Begin DL485-Serial plugin", "-" * 50, end="\n")
config_file_name = "/home/pi/domoticz/plugins/DL485_DOMOTICZ/config.json"  # File di configurazione
logstate = 2 # 0==Debug disabilitato, 1==scrivi su log, 2==stampa a video
b = Bus(config_file_name, logstate)  # Istanza la classe Bus
# log = Log()  # Istanza la classe Log

DevicesCreate = {} # DICT con tutti i dispositivi DL485 creati

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
        self.devices = { # DICT with all devices
            'Unit2DeviceID': {},
            'DeviceID2Unit': {},
        } 

        self.typeNameDict = {   
            'None'                              : {},     
            'Temperature'                       : { 'Type': 80,         'SubType': 5,       'SwitchType': 0},
            'Humidity'                          : { 'Type': 81,         'SubType': 1,       'SwitchType': 0},
            'Temp+Hum'                          : { 'Type': 82,         'SubType': 1,       'SwitchType': 0},
            'Temp+Hum+Baro'                     : { 'Type': 84,         'SubType': 1,       'SwitchType': 0},
            'Temp+Hum+Baro2'                    : { 'Type': 84,         'SubType': 2,       'SwitchType': 0},
            'Weather Station Temp+Hum+Baro'     : { 'Type': 84,         'SubType': 16,      'SwitchType': 0},
            'Rain'                              : { 'Type': 85,         'SubType': 1,       'SwitchType': 0},
            'Wind'                              : { 'Type': 86,         'SubType': 1,       'SwitchType': 0},
            'UV'                                : { 'Type': 87,         'SubType': 1,       'SwitchType': 0},
            'Ampere (3 Phase)'                  : { 'Type': 89,         'SubType': 1,       'SwitchType': 0},
            'Scale Weight'                      : { 'Type': 93,         'SubType': 1,       'SwitchType': 0},
            'Counter'                           : { 'Type': 113,        'SubType': 0,       'SwitchType': 0},
            'RGBW'                              : { 'Type': 241,        'SubType': 1,       'SwitchType': 0},
            'RGB'                               : { 'Type': 241,        'SubType': 2,       'SwitchType': 7},
            'White'                             : { 'Type': 241,        'SubType': 3,       'SwitchType': 0},
            'RGBWW'                             : { 'Type': 241,        'SubType': 4,       'SwitchType': 0},
            'RGBWZ'                             : { 'Type': 241,        'SubType': 6,       'SwitchType': 0},
            'RGBWWZ'                            : { 'Type': 241,        'SubType': 7,       'SwitchType': 0},
            'Cold white+Warm white'             : { 'Type': 241,        'SubType': 8,       'SwitchType': 0},
            'Setpoint'                          : { 'Type': 242,        'SubType': 1,       'SwitchType': 0},
            'General Visibility'                : { 'Type': 243,        'SubType': 1,       'SwitchType': 0},
            'General Solar Radiation'           : { 'Type': 243,        'SubType': 2,       'SwitchType': 0},
            'General Solar Moisture'            : { 'Type': 243,        'SubType': 3,       'SwitchType': 0},
            'General Leaf Wetness'              : { 'Type': 243,        'SubType': 4,       'SwitchType': 0},
            'General Percentage'                : { 'Type': 243,        'SubType': 6,       'SwitchType': 0},
            'Voltage'                           : { 'Type': 243,        'SubType': 8,       'SwitchType': 0}, # General Voltage
            'General Pressure'                  : { 'Type': 243,        'SubType': 9,       'SwitchType': 0},
            'Text'                              : { 'Type': 243,        'SubType': 19,      'SwitchType': 0}, # General Text
            'General Alert'                     : { 'Type': 243,        'SubType': 22,      'SwitchType': 0},
            'Current (Single)'                  : { 'Type': 243,        'SubType': 23,      'SwitchType': 0}, # General Ampere (1 Phase)
            'General Sound Level'               : { 'Type': 243,        'SubType': 24,      'SwitchType': 0},
            'General Barometer'                 : { 'Type': 243,        'SubType': 26,      'SwitchType': 0},
            'General Distance'                  : { 'Type': 243,        'SubType': 27,      'SwitchType': 0},
            'Counter Incremental'               : { 'Type': 243,        'SubType': 28,      'SwitchType': 0}, # General Counter Incremental
            'kWh'                               : { 'Type': 243,        'SubType': 29,      'SwitchType': 0}, # General kWh
            'General Waterflow'                 : { 'Type': 243,        'SubType': 30,      'SwitchType': 0},
            'Custom Sensor'                     : { 'Type': 243,        'SubType': 31,      'SwitchType': 0},
            'General Managed counter Energy'    : { 'Type': 243,        'SubType': 33,      'SwitchType': 0},
            'General Managed counter Gas'       : { 'Type': 243,        'SubType': 33,      'SwitchType': 1},
            'General Managed counter Water'     : { 'Type': 243,        'SubType': 33,      'SwitchType': 2},
            'General Managed counter Counter'   : { 'Type': 243,        'SubType': 33,      'SwitchType': 3},
            'General Managed counter Energy Generated': {'Type': 243,   'SubType': 33,      'SwitchType': 4},
            'General Managed counter Time'      : { 'Type': 243,        'SubType': 33,      'SwitchType': 5},
            'Switch'                            : { 'Type': 244,        'SubType': 62,      'SwitchType': 0}, # Selector Switch On/Off
            'Selector Switch Doorbell'          : { 'Type': 244,        'SubType': 62,      'SwitchType': 1},
            'Selector Switch Contact'           : { 'Type': 244,        'SubType': 62,      'SwitchType': 2},
            'Selector Switch Blinds'            : { 'Type': 244,        'SubType': 62,      'SwitchType': 3},
            'Selector Switch X10 Siren'         : { 'Type': 244,        'SubType': 62,      'SwitchType': 4},
            'Selector Switch Smoke Detector'    : { 'Type': 244,        'SubType': 62,      'SwitchType': 5},
            'Selector Switch Blinds Inverted'   : { 'Type': 244,        'SubType': 62,      'SwitchType': 6},
            'Selector Switch Dimmer'            : { 'Type': 244,        'SubType': 73,      'SwitchType': 7},
            'Selector Switch Motion Sensor'     : { 'Type': 244,        'SubType': 62,      'SwitchType': 8},
            'Selector Switch Push On Button'    : { 'Type': 244,        'SubType': 62,      'SwitchType': 9},
            'Selector Switch Push Off Button'   : { 'Type': 244,        'SubType': 62,      'SwitchType': 10},
            'Switch Door Contact'               : { 'Type': 244,        'SubType': 62,      'SwitchType': 11},
            'Switch Dusk Sensor'                : { 'Type': 244,        'SubType': 62,      'SwitchType': 12},
            'Switch Blinds Percentage'          : { 'Type': 244,        'SubType': 62,      'SwitchType': 13},
            'Switch Venetian Blinds US'         : { 'Type': 244,        'SubType': 62,      'SwitchType': 14},
            'Switch Venetian Blinds EU'         : { 'Type': 244,        'SubType': 62,      'SwitchType': 15},
            'Switch Blinds Percentage Inverted' : { 'Type': 244,        'SubType': 62,      'SwitchType': 16},
            'Switch Media Player'               : { 'Type': 244,        'SubType': 62,      'SwitchType': 17},
            'Switch Selector'                   : { 'Type': 244,        'SubType': 62,      'SwitchType': 18},
            'Switch Door Lock'                  : { 'Type': 244,        'SubType': 62,      'SwitchType': 19},
            'Switch Door Lock Inverted'         : { 'Type': 244,        'SubType': 62,      'SwitchType': 20},
            'Illumination'                      : { 'Type': 246,        'SubType': 1,      'SwitchType': 0}, # Lux
            'Temp+Baro'                         : { 'Type': 247,        'SubType': 1,      'SwitchType': 0},
            'Usage Electric'                    : { 'Type': 248,        'SubType': 1,      'SwitchType': 0},
            'Air Quality'                       : { 'Type': 249,        'SubType': 1,      'SwitchType': 0},
            'P1 Smart Meter Energy'             : { 'Type': 250,        'SubType': 1,      'SwitchType': 0},
            'P1 Smart Meter Gas'                : { 'Type': 246,        'SubType': 1,      'SwitchType': 0},
        }

        self.nValueDict = { # Significato dei valori nValue di Switch:
            0: "Off",
            1: "On",
            2: "sValue",
            3: "Group Off",
            4: "Group On",
            5: "Set Group Level sValue",
            6: "Dim",
            7: "Gright",
            8: "Sound 0",
            9: "Sound 1",
            10: "Sound 2",
            11: "Sound 3",
            12: "Sound 4",
            13: "Sound 5",
            14: "Sound 6",
            15: "Sound 7",
            16: "Sound 8",
            17: "Stop",
            18: "Program",
        }

        b.system = 'Domoticz' # Indica alla classe chi la stà istanziando

        # b.TXmsg = [b.getBoardType(0)] # Chiede ai nodi di inviare in rete le loro caratteristiche

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

    def devicesUpdate(self):
        """ Dizionario self.devices con tutti i device presenti in domoticz """
        for d in Devices:
            self.devices['Unit2DeviceID'][Devices[d].Unit] = Devices[d].DeviceID
            self.devices['DeviceID2Unit'][Devices[d].DeviceID] = Devices[d].Unit

    def onStart(self):
        self.debug = int(Parameters["Mode6"])
        Domoticz.Debugging(self.debug)
        b.log.logstate = self.debug & 3
        Domoticz.Log("Start DL485 Loop Plugin with Debug: {}".format(self.debug))

        for board_id in b.mapiotype: # Iterazione di tutte le board su config.json
            self.devicesUpdate() # Aggiorna dizionario con i device di domoticz

            # Creazione dispositivi TEXT per ciascuna Board per inserire le caratteristiche del nodo
            DeviceID = "{}-0".format(board_id)
            board_enable = b.config['BOARD{}'.format(board_id)]['GENERAL_BOARD'].get('enable', 1)
            if DeviceID not in self.devices['DeviceID2Unit'].keys():
                """ Create Devices 0 con le caratteristiche della scheda """                    
                # print("Crea il device TEXT con le caratteristiche della BOARD: {}".format(board_id))
                unit_present = list(self.devices['Unit2DeviceID'].keys())                
                Unit = self.unitPresent(unit_present)    
                dtype = 'Text'
                name = 'BOARD{} CHARACTERISTICS'.format(board_id)
                description = "Caratteristiche Board {}".format(board_id)

                Domoticz.Device(DeviceID=DeviceID, Name=name, Unit=Unit, Type=self.typeNameDict[dtype]['Type'], Subtype=self.typeNameDict[dtype]['SubType'], \
                    Description=description, Switchtype=self.typeNameDict[dtype]['SwitchType'], Image=0, Options={}, Used=board_enable).Create()
                
                self.devices['Unit2DeviceID'][Unit] = DeviceID
                self.devices['DeviceID2Unit'][DeviceID] = Unit
            else:
                # print("Update device TEXT con le caratteristiche della BOARD: {}".format(board_id))
                Unit = self.devices['DeviceID2Unit'][DeviceID]
                board_enable = b.config['BOARD{}'.format(board_id)]['GENERAL_BOARD'].get('enable', 1)
                Devices[Unit].Update(Used=board_enable, nValue=0, sValue='')
           
            for logic_io in b.mapiotype[board_id]: # iterazione per ogni logic_io
                self.devicesUpdate() # Aggiorna dizionario con i device di domoticz

                description = b.mapiotype[board_id][logic_io]['description']
                device_enable = b.mapiotype[board_id][logic_io]['enable'] and b.mapiotype[board_id][logic_io]['board_enable'] # Abilita il device se sulla configurazione sono abilitati
                device_type = b.mapiotype[board_id][logic_io]['device_type']
                dtype = b.mapiotype[board_id][logic_io]['dtype']
                DeviceID = "{}-{}".format(board_id, logic_io)
                # print("----- board_id: {}, logic_io: {}, board_enable: {}, device_type: {}".format(board_id, logic_io, board_enable, device_type))

                if device_type in ['DIGITAL_IN_PULLUP', 'DIGITAL_IN']:
                    image = 9
                elif device_type in ['DIGITAL_OUT']:
                    image = 0
                else:
                    image = 0

                
                name = "[{}] {}".format(DeviceID, b.mapiotype[board_id][logic_io]['name'])
                
                # print("*** BoardID:{:>2} LogiIO:{:>3}  Device_enable:{:>3}  DeviceID:{:>6}".format(board_id, logic_io, device_enable, DeviceID))

                if dtype not in self.typeNameDict:
                    Domoticz.Log("            ==>> ERROR DEVICE dtype: {} on board_id:{} logic_io:{} is NOT CORRECT!!!".format(dtype, board_id, logic_io))
                    sys.exit()
                    # continue
                
                if dtype == "None":
                    # Domoticz.Log("            ==>> ERROR DEVICE dtype NON IMPOSTATO: None => Board_id:{} Logic_io: {}".format(board_id, logic_io))
                    # sys.exit()
                    continue

                Type = self.typeNameDict[dtype]['Type']
                SubType = self.typeNameDict[dtype]['SubType']                    
                SwitchType = self.typeNameDict[dtype]['SwitchType']
                
                options = ''
                # value = 0
                
                if dtype == 'switch':
                    pass
                elif dtype == 'Temp+Hum':
                    sValue = "0;0;0"
                elif dtype == 'Temp+Hum+Baro':
                    sValue = "0;0;0;0;0"
                elif dtype == 'kWh':
                    sValue = "0;0"
                elif dtype == 'Custom Sensor':
                    options = {'Custom': '1;{}'.format(b.mapiotype[board_id][logic_io]['dunit'])}
                    sValue = "0"
                elif dtype == 'Counter Incremental': # mostra i Watt/ora
                    sValue = "0"
                elif dtype == 'None':
                    # print("Device che non deve essere aggiunto a Domoticz")
                    continue
                

                # print("====>>>>> Device: Unit:{:<3} Dtype: {:20}    nValue: {:<3}    sValue: {:<5}  Used: {} OPTIONS: {} Name: {:30}".format(Unit, dtype, value, sValue, device_enable, options, name))
                
                # print(DeviceID, self.devices['DeviceID2Unit'].keys())
                if DeviceID not in self.devices['DeviceID2Unit'].keys():
                    """ Crea Device """
                    unit_present = list(self.devices['Unit2DeviceID'].keys())
                    Unit = self.unitPresent(unit_present)
                    
                    ### Domoticz.Device(Name=name, Unit=Unit, TypeName=dtype, Description=description, DeviceID=DeviceID, Used=device_enable, Image=image).Create()
                    
                    Domoticz.Device(DeviceID=DeviceID, Name=name, Unit=Unit, Type=Type, Subtype=SubType, Switchtype=SwitchType, Description=description, Image=0, \
                        Options={}, Used=device_enable).Create()

                    self.devices['Unit2DeviceID'][Unit] = DeviceID
                    self.devices['DeviceID2Unit'][DeviceID] = Unit
                    
                    Domoticz.Log("====>>>>> Create Device: Unit:{:5} DeviceID:{:>5} Dtype: {:20}    Used: {} OPTIONS: {}    Name: {:30}"
                        .format(Unit, DeviceID, dtype, device_enable, options, name))

                Unit = self.devices['DeviceID2Unit'][DeviceID]

                if not b.overwrite_text and Devices[Unit].Description != description:  # check if Domoticz description is equal to config description
                    description = Devices[Unit].Description

                if not b.overwrite_text and Devices[Unit].Name != name:  # check if Domoticz description is equal to config description
                    name = Devices[Unit].Name

                Domoticz.Log("=> Update Dev: Un:{:3} DevID:{:>4} T:{:>3} SubT:{:>3} SwitchT:{:>3} Dtype: {:20} nVal: {:<1} sVal: {:>4} Used: {} opt: {:<10} Name: {:30}"
                    .format(Unit, DeviceID, Type, SubType, SwitchType, dtype, Devices[Unit].nValue, Devices[Unit].sValue, device_enable, str(options), name))
                
                Devices[Unit].Update(Name=name, Type=Type, Subtype=SubType, Switchtype=SwitchType, Description=description, nValue=Devices[Unit].nValue, sValue=Devices[Unit].sValue, Used=device_enable, Options=options)
                
        b.Connection = Domoticz.Connection(Name="DL485", Transport="Serial", Address=b.bus_port, Baud=b.bus_baudrate)
        b.Connection.Connect()

    def onStop(self):
        if b.telegram_enable: # Telegram is activated
            pass # To do
        Domoticz.Log("{} {}".format("onStop DL485-SERIAL plugin", self))

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("{} {} {} {} {}".format("onConnect DL485-SERIAL plugin", self, Connection, Status, Description))

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
            print("            CHIAVE NON TROVATA SUL DICT IO di DOMOTICZ: {}".format(DeviceID))
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

                # if linked_proc and plc_function == 'disable' and 1==2: # Da rifare perché non FUNZIONA
                #     """
                #         elenco linked proc
                #         toggle
                #         direct (accetta un solo ingresso e lo replica direttamente)
                #         invert (accetta un solo ingresso e lo replica invertito)
                #         and (n ingressi in and)
                #         or
                #         xor
                #         nand
                #         nor
                #         nxor
                #     """

                #     for x_out in linked_proc:
                #         x_outa = x_out.split("-")
                #         x_board_id = int(x_outa[0])
                #         x_logic_io = int(x_outa[1])

                #         app_linked_proc = linked_proc["%s-%s" %(x_outa[0], x_outa[1])]['linked_proc']

                #         if app_linked_proc == 'toggle':
                #             if x_value & 0b100:
                #                 value = b.status[x_board_id]['io'][x_logic_io - 1]
                #                 value = 1 - value

                #                 value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                #                 # print("TOGGLE", x_out, value)
                #                 msg = b.writeIO(x_board_id, x_logic_io, [value])
                #                 b.TXmsg.append(msg)

                #         elif app_linked_proc == 'direct':
                #             value = x_value & 1
                #             value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                #             # print("DIRECT", x_out, value)
                #             msg = b.writeIO(x_board_id, x_logic_io, [value])
                #             b.TXmsg.append(msg)

                #         elif app_linked_proc == 'invert':
                #             value = (x_value & 1) ^ 1
                #             value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                #             # print("INVERT", x_out, value)
                #             msg = b.writeIO(x_board_id, x_logic_io, [value])
                #             b.TXmsg.append(msg)
                #         elif app_linked_proc == 'and':
                #             linked_board_id_logic_io = b.mapiotype[x_board_id][x_logic_io]['linked_board_id_logic_io']
                #             # print("linked_board_id_logic_io", linked_board_id_logic_io)
                #             value = 1
                #             for ii in linked_board_id_logic_io:
                #                 ii_outa = ii.split("-")
                #                 ii_board_id = int(ii_outa[0])
                #                 ii_logic_io = int(ii_outa[1])
                #                 value = value & b.status[ii_board_id]['io'][ii_logic_io - 1]
                #             value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                #             msg = b.writeIO(x_board_id, x_logic_io, [value])
                #             b.TXmsg.append(msg)

                #         elif app_linked_proc == 'or':
                #             linked_board_id_logic_io = b.mapiotype[x_board_id][x_logic_io]['linked_board_id_logic_io']
                #             value = 0
                #             for ii in linked_board_id_logic_io:
                #                 ii_outa = ii.split("-")
                #                 ii_board_id = int(ii_outa[0])
                #                 ii_logic_io = int(ii_outa[1])
                #                 value = value | b.status[ii_board_id]['io'][ii_logic_io - 1]
                #             value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                #             msg = b.writeIO(x_board_id, x_logic_io, [value])
                #             b.TXmsg.append(msg)
                #         elif app_linked_proc == 'xor':
                #             linked_board_id_logic_io = b.mapiotype[x_board_id][x_logic_io]['linked_board_id_logic_io']
                #             value = 0
                #             for ii in linked_board_id_logic_io:
                #                 ii_outa = ii.split("-")
                #                 ii_board_id = int(ii_outa[0])
                #                 ii_logic_io = int(ii_outa[1])
                #                 value = value ^ b.status[ii_board_id]['io'][ii_logic_io - 1]
                #             value = b.make_inverted(x_board_id, x_logic_io, value)  # Inverte l'IO se definito sul file di configurazione
                #             msg = b.writeIO(x_board_id, x_logic_io, [value])
                #             b.TXmsg.append(msg)

            elif dtype == "Selector Switch Dimmer": # Dimmer
                b.status[board_id]['io'][logic_io - 1] = value
                sValue = int(round(value * 0.3922))
                nValue = 2 if value else 0
                # print(f"===>>>     DIMMER {board_id}-{logic_io} - value:{value} - nValue:{nValue} - sValue:{sValue}")
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue))

            elif dtype == "RGB": # RGB
                # Da fare
                print(f"=*****==>>>     RGB {board_id}-{logic_io}", value)
                # pprint(b.mapiotype[board_id][logic_io])
                # b.status[board_id]['io'][logic_io - 1] = value
                # sValue = int(round(value * 0.3922))
                # nValue = 2 if value else 0
                
                # Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            
            
            elif dtype == 'Voltage':
                sValue = str(value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue=int(value), sValue=sValue)

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
                            value_humidity = b.status[board_id_linked]['io'][logic_io_linked - 1]

                            if value_humidity:
                                DeviceIDLinked = '%s-%s' %(board_id_linked, logic_io_linked)
                                if DeviceIDLinked not in self.devices['DeviceID2Unit']: return

                                # print(">>>>>>>>>>>>>>>>>>>>>>PSYCHROMETER DEVICE:", DeviceIDLinked)
                                UnitLinked = self.devices['DeviceID2Unit'][DeviceIDLinked]

                                # dtypeLinked = b.mapiotype[board_id_linked][logic_io_linked]['dtype']
                                if value_humidity < 40:
                                    hum_status = 2
                                elif value_humidity >=45 and value_humidity < 56:
                                    hum_status = 1
                                elif value_humidity >=60:
                                    hum_status = 3
                                else:
                                    hum_status = 0

                                # print(UnitLinked, dtypeLinked)
                                Domoticz.Log("Device:{}-{} value:{} {}".format(board_id, logic_io, value, device_type_linked))
                                Devices[UnitLinked].Update(nValue = int(value_humidity), sValue = '{}'.format(hum_status))

                    b.status[board_id]['io'][logic_io - 1] = value
                    Devices[Unit].Update(nValue = 0, sValue = sValue)

            elif dtype == 'Temp+Hum+Baro':
                if not value:
                    return
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

            elif dtype == 'Illumination':
                # b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = value, sValue = str(value))

            # elif dtype == 'Counter Incremental':
                # print("==>>>", board_id, logic_io, value)
                # b.status[board_id]['io'][logic_io - 1] = value
                # Devices[Unit].Update(nValue = int(value)&1, sValue = str(int(value)&1))

            elif dtype == "kWh":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                # str(en_0)+";"+str(en_1 * 1000)
                Devices[Unit].Update(nValue=0, sValue="{};{}".format(value, value))

            elif dtype == "Counter Incremental":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = value, sValue = str(value))

            elif dtype == "Current (Single)" or dtype == "Electric":
                if not value:
                    return 0
                b.status[board_id]['io'][logic_io - 1] = value
                
                # print('------------', board_id, logic_io, value)
                Devices[Unit].Update(nValue = int(value), sValue="{};{}".format(value, 10))


            elif dtype == "Custom Sensor":
                # print("Custom Sensor", value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = int(value), sValue="{}".format(value))

            elif dtype == "Current/Ampere": # Triphase
                pass

            elif dtype == "Text": # Triphase
                print("            ==>> DEVICE TEXT ancora da fare", board_id, logic_io, value)
            
            else:
                # print(" NON MAPPATO ", board_id, logic_io, value, dtype)
                Domoticz.Log("DEVICE non MAPPATO      {}-{} value:{} Device DTYPE non MAPPATO / ERRATO: {:20}    ".format(board_id, logic_io, value, dtype))

            Domoticz.Log("  {}-{} value:{}  Device:{:20}".format(board_id, logic_io, value, dtype))

    def onCommand(self, Unit, Command, Level, Hue):
        print(f"===>>> onCommand: Unit:{Unit}, Command:{Command}, Level:{Level}, Hue:{Hue}")
        bio = Devices[Unit].DeviceID.split("-")
        board_id = int(bio[0])
        logic_io = int(bio[1])
        if Command == 'Off':
            value = 0
        elif Command == 'On':
            value = 1
            if "plc_function" in b.mapiotype[board_id][logic_io] and b.mapiotype[board_id][logic_io]["plc_function"] == 'dimmer':
                value = int(Level * 2.55)
        elif Command == 'Set Level':
            if "plc_function" in b.mapiotype[board_id][logic_io] and b.mapiotype[board_id][logic_io]["plc_function"] == 'dimmer':
                value = int(Level * 2.55)
            else:
                value = Level
        elif Command == 'Set Color':
            
            Hue = eval(Hue) # String to dict
            # red = Hue['r']
            # green = Hue['g']
            # blue = Hue['b']
            for k in Hue:
                if k == 'r':
                    print("RED:", Hue[k])
                    msg = b.writeIO(board_id, 1, [Hue[k]])
                    b.TXmsg.append(msg)
                elif k == 'g':
                    print("GREEN:", Hue[k])
                    msg = b.writeIO(board_id, 2, [Hue[k]])
                    b.TXmsg.append(msg)
                elif k == 'b':
                    print("BLUE:", Hue[k])
                    msg = b.writeIO(board_id, 3, [Hue[k]])
                    b.TXmsg.append(msg)
            value = Level
        else:
            print("================== Command NON DEFINITO", Command)


        msg = b.writeIO(board_id, logic_io, [value])
        # print("MSG:", msg)
        b.TXmsg.append(msg)

    def onMessage(self, Connection, RXbytes):
        for d in RXbytes:
            b.RXtrama = b.readSerial(d)
            b.cron()
            if not b.RXtrama: continue

            b.arrivatatrama()

            if len(b.RXtrama)>1 and b.RXtrama[1] == b.code['CR_GET_BOARD_TYPE'] | 32: # Risposta con infomrazioni delle varie Board
                board_id = b.RXtrama[0]
                msg = "Configurazione della BOARD{}:\n".format(board_id)
                msg += 'Board Type: {}\n'.format(b.get_board_type[board_id]['board_type'])
                msg += 'Data Firmware: {}\n'.format(b.get_board_type[board_id]['data_firmware'])
                msg += 'I/O Numbers: {}\n'.format(b.get_board_type[board_id]['io_number'])
                msg += 'I2C: {}\n'.format(b.get_board_type[board_id]['i2c'])
                msg += 'One Wire: {}\n'.format(b.get_board_type[board_id]['onewire'])
                msg += 'Dimmer: {}\n'.format(b.get_board_type[board_id]['dimmer'])
                msg += 'PLC: {}\n'.format(b.get_board_type[board_id]['plc'])
                msg += 'Power On: {}\n'.format(b.get_board_type[board_id]['power_on'])
                msg += 'PWM: {}\n'.format(b.get_board_type[board_id]['pwm'])
                msg += 'RFID: {}\n'.format(b.get_board_type[board_id]['rfid'])
                msg += 'PRO: {}\n'.format(b.get_board_type[board_id]['protection'])
                

                # pprint(b.get_board_type[board_id])
                if len(b.get_board_type[board_id]) == 14: # Informazioni su nuove schede
                    msg += 'RMS_POWER: {}\n'.format(b.get_board_type[board_id]['rms_power'])
                    msg += 'N. ERROR CONFLICT: {}\n'.format(b.get_board_type[board_id]['error_conflict'])
                    msg += 'N. ERROR IO: {}\n'.format(b.get_board_type[board_id]['error_logic_io_fisic_io'])

                try:
                    Unit = self.devices['DeviceID2Unit']["{}-0".format(b.RXtrama[0])]
                    Devices[Unit].Update(nValue=1, sValue=msg)
                except:
                    print("            ==>> ERROR: Board ID {} non impostata su Domoticz".format(b.RXtrama[0]))
                
                # Devices[Unit].Update(nValue = 0, sValue = sValue)

            # print(b.RXtrama) # Non togliere altrimenti non funziona
            if len(b.RXtrama) > 1:  # ERA 1 Mosra solo comunicazioni valide (senza PING)
                # print("Trama arrivata:", b.RXtrama, b.int2hex(b.RXtrama))
                # if (b.RXtrama[1] & 0xDF) in b.code: # comando valido o feedback a comando valido

                # if b.RXtrama[1] & 0xDF == b.code['COMUNICA_IO']:  # COMUNICA_IO / Scrive valore USCITA
                if b.RXtrama[1] in [ b.code['COMUNICA_IO'], b.code['RFID'] ]:  # COMUNICA_IO / Scrive valore USCITA                    
                    # print("onMessage>>>", b.RXtrama, "RxValue:", b.RXtrama[3:])
                    value = b.calculate(b.RXtrama[0], b.RXtrama[1], b.RXtrama[2], b.RXtrama[3:])  # Aggiorna DOMOTICZ
                    # print("VALUE::", value)
                    self.updateIO(b.RXtrama[0], b.RXtrama[2], value)  # Aggiorna DOMOTICZ

                    # print("VALUE CALCULATE:", b.RXtrama[0], b.RXtrama[2], b.RXtrama[3:], value)
                elif b.RXtrama[1] == b.code['CR_GET_BOARD_TYPE'] | 32:
                    # print("===>>>>> GET BOARD ID", b.getBoardType)
                    pass
                else:
                    pass
                    # print("{:<7}  NO COMUNICA IO         {}".format(b.nowtime, b.RXtrama))

            # b.writeLog()

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("{} {} {} {} {} {} {} {} {}".format("onNotification DL485-SERIAL plugin", self, Name, Subject, Text, Status, Priority, Sound, ImageFile))

    def onDisconnect(self, Connection):
        Domoticz.Log("{} {} {}".format("onDisconnect DL485-SERIAL plugin", self, Connection))

    def onHeartbeat(self):
        # Domoticz.Log("{} {}".format("onHeartbeat DL485-SERIAL plugin", self))
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

def DumpConfigToLog():
    return
