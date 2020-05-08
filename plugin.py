"""
<plugin key="DLBOARD" name="DL Board plugin - SERIAL" author="Luca Subiaco e Daniele Gava" version="1.1" externallink="https://www.dmocontrol.info/" wikilink="https://www.domocontrol.info">
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

# import threading
# import queue


print("-" * 50, "Begin DL485-Serial plugin", "-" * 50, end="\n")
config_file_name = "/home/pi/domoticz/plugins/DL485_DOMOTICZ/config.json"  # File di configurazione
logstate = 2 # Abilita la stampa del DEBUG: 1==scrivi su log, 2==stampa a video
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
        # self.messageQueue = queue.Queue()
        # self.messageThread = threading.Thread(name="QueueThread", target=BasePlugin.handleMessage, args=(self,))

        self.debug = 0
        self.devices = { # DICT with all devices
            'Unit2DeviceID': {},
            'DeviceID2Unit': {},
        } 

        self.typeName = [
            "Air Quality",
            "Alert",
            "Barometer",
            "Counter Incremental",
            "Contact",
            "Current/Ampere",
            "Current (Single)",
            "Custom",
            "Dimmer",
            "Distance",
            "Gas",
            "Humidity",
            "Illumination",
            "kWh",
            "Leaf Wetness",
            "Motion",
            "Percentage",
            "Push On",
            "Push Off",
            "Pressure",
            "Rain",
            "Selector Switch",
            "Soil Moisture",
            "Solar Radiation",
            "Sound Level",
            "Switch",
            "Temperature",
            "Temp+Hum",
            "Temp+Hum+Baro",
            "Text",
            "Usage",
            "UV",
            "Visibility",
            "Voltage",
            "Waterflow",
            "Wind",
            "Wind+Temp+Chill",
            "None",
        ]

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

    def onStart(self):
        self.debug = int(Parameters["Mode6"])
        Domoticz.Debugging(self.debug)

        Domoticz.Log("Debugger started, use 'telnet 0.0.0.0 4444' to connect")
        # import rpdb
        # rpdb.set_trace()

        Domoticz.Log("Start DL485 Loop Plugin with Debug: {}".format(self.debug))

        for d in Devices:
            print("DEVICES:", Devices[d])
            self.devices['Unit2DeviceID'][Devices[d].Unit] = Devices[d].DeviceID
            self.devices['DeviceID2Unit'][Devices[d].DeviceID] = Devices[d].Unit

        for k in b.config.keys(): # Per Board Type descriptions
            if "BOARD" in k:
                if b.config[k]['GENERAL_BOARD']['enable'] == 1:
                    print("BOARD::", b.config[k]['GENERAL_BOARD']['enable'])  
                    
        for board_id in b.mapiotype:
            
            # pprint(self.devices)
            
            # Creazione dispositivi TEXT per ciascuna Board per inserire le caratteristiche del nodo
            Device_board_characteristics = "{}-0".format(board_id)
            # print("Device_board_characteristics", Device_board_characteristics)
            if Device_board_characteristics not in self.devices['DeviceID2Unit'].keys():
                unit_present = list(self.devices['Unit2DeviceID'].keys())
                Unit = self.unitPresent(unit_present)
                name = 'BOARD{} CHARACTERISTICS'.format(board_id)
                dtype = 'Text'
                description = "Caratteristiche della Board {}".format(board_id)
                # print("Device_board_characteristics", Device_board_characteristics, unit_present, Unit, name, dtype, description)
                Domoticz.Device(Name=name, Unit=Unit, TypeName=dtype, Description=description, DeviceID=Device_board_characteristics, Used=True, Image=0).Create()
                self.devices['Unit2DeviceID'][Unit] = Device_board_characteristics
                self.devices['DeviceID2Unit'][Device_board_characteristics] = Unit

            for logic_io in b.mapiotype[board_id]:
                board_enable = b.mapiotype[board_id][logic_io]['board_enable']
                io_enable = b.mapiotype[board_id][logic_io]['enable']
                device_enable = board_enable & io_enable
                device_type = b.mapiotype[board_id][logic_io]['device_type']
                overwrite_text = b.mapiotype[board_id][logic_io]['overwrite_text'] # if 1 overtwrite text name and description with config.json
                # print("DeviceType:", device_type)
                if device_type in ['DIGITAL_IN_PULLUP', 'DIGITAL_IN']:
                    image = 9
                elif device_type in ['DIGITAL_OUT']:
                    image = 0
                else:
                    image = 0

                DeviceID = "{}-{}".format(board_id, logic_io)
                
                name = "[{}] {}".format(DeviceID, b.mapiotype[board_id][logic_io]['name'])
                description = b.mapiotype[board_id][logic_io]['description']
                dtype = b.mapiotype[board_id][logic_io]['dtype']
                device_enable = b.mapiotype[board_id][logic_io]['enable']

                # print("*** BID:{} IOID:{} - logic_io:{} Board_enable:{} - Domoticz Device ENABLE:{} - DeviceID:{}".format(board_id, board_enable, logic_io, io_enable, device_enable, DeviceID))

                if dtype not in self.typeName:
                    Domoticz.Log("========>>>>>>>>>>>>>>>>>>> ERROR DEVICE dtype: {}. Device name is NOT CORRECT!!!".format(dtype))

                if dtype == "None":
                    continue
                # print(">>>>>>>>>>>>>>><DTYPE", dtype)

                if DeviceID not in self.devices['DeviceID2Unit'].keys():
                    unit_present = list(self.devices['Unit2DeviceID'].keys())
                    Unit = self.unitPresent(unit_present)
                    Domoticz.Device(Name=name, Unit=Unit, TypeName=dtype, Description=description, DeviceID=DeviceID, Used=device_enable, Image=image).Create()
                    self.devices['Unit2DeviceID'][Unit] = DeviceID
                    self.devices['DeviceID2Unit'][DeviceID] = Unit
                    Domoticz.Log("Create Device: Name:{:10}    Dtype:{:10}    Used:{}".format(name, dtype, device_enable))

                value = int(b.mapiotype[board_id][logic_io]['default_startup_value']) if 'default_startup_value' in b.mapiotype[board_id][logic_io] else 0
                sValue = 'On' if value else 'Off'

                if dtype == 'switch':
                    pass
                elif dtype == 'Temp+Hum':
                    sValue = "0;0;0"
                elif dtype == 'Temp+Hum+Baro':
                    sValue = "0;0;0;0;0"
                elif dtype == 'kWh':
                    sValue = "0;0"
                elif dtype == 'Custom Sensor':
                    sValue = "0"
                elif dtype == 'Counter Incremental': # mostra i Watt/ora
                    sValue = "0"
                elif dtype == 'None':
                    print("Device che non deve essere aggiunto a Domoticz")
                    continue

                Unit = self.devices['DeviceID2Unit'][DeviceID]

                if not overwrite_text and Devices[Unit].Description != description:  # check if Domoticz description is equal to config description
                    description = Devices[Unit].Description

                if not overwrite_text and Devices[Unit].Name != name:  # check if Domoticz description is equal to config description
                    name = Devices[Unit].Name

                Devices[Unit].Update(Name=name, TypeName=dtype, Description=description, nValue=value, sValue=sValue, Used=device_enable)
                Domoticz.Log("Update Device: Dtype:{:20}    nValue{:5}    sValue:{:7}    Used:{}    Name:{:30}".format(dtype, value, sValue, device_enable, name))

        # self.SerialConn = Domoticz.Connection(Name="DL485", Transport="Serial", Address = Parameters["SerialPort"], Baud = int(Parameters["Mode3"]))
        # self.SerialConn = Domoticz.Connection(Name="DL485", Transport="Serial", Address=b.bus_port, Baud=b.bus_baudrate)
        b.Connection = Domoticz.Connection(Name="DL485", Transport="Serial", Address=b.bus_port, Baud=b.bus_baudrate)
        
        # self.SerialConn.Connect()
        b.Connection.Connect()

        # configuration = b.getConfiguration()  # Set configuration of boards
        # b.TXmsg = configuration # Mette trama configurazione in lista da inviare
        # b.TXmsg += [b.getBoardType(0)] # Request GetTypeBoard Informations
        

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

            elif dtype == 'Counter Incremental':
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = value&1, sValue = str(value&1))

            elif dtype == "kWh":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                # str(en_0)+";"+str(en_1 * 1000)
                Devices[Unit].Update(nValue=0, sValue="{};{}".format(value, value))

            elif dtype == "Counter Incremental":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = value, sValue = str(value))

            elif dtype == "Current (Single)":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = int(value), sValue="{};{}".format(value, 10))

            elif dtype == "Custom Sensor":
                # value = b.calculate(board_id, logic_io, value)
                b.status[board_id]['io'][logic_io - 1] = value
                Devices[Unit].Update(nValue = int(value), sValue="{}".format(value))

            elif dtype == "Current/Ampere": # Triphase
                pass
            
            elif dtype == "Text": # Triphase
                print("DEVICE TEXT ancora da fare", board_id, logic_io, value)
            
            elif dtype == "None":
                print("DEVICE None ancora da fare", board_id, logic_io, value)

            else:
                Domoticz.Log("{             DEVICE non MAPPATO      {}-{} value:{} Device DTYPE non MAPPATO / ERRATO: {:20}    ".format(b.nowtime, board_id, logic_io, value, dtype))

            Domoticz.Log("  {}-{} value:{}  Device:{:20}".format(board_id, logic_io, value, dtype))

    def onCommand(self, Unit, Command, Level, Hue):
        # print("onCommand", Unit, Command, Level, Hue)
        bio = Devices[Unit].DeviceID.split("-")
        board_id = int(bio[0])
        logic_io = int(bio[1])
        value = 1 if Command == 'On' else 0
        msg = b.writeIO(board_id, logic_io, [value])
        b.TXmsg.append(msg)

    def onMessage(self, Connection, RXbytes):
        for d in RXbytes:
            b.RXtrama = b.readSerial(d)

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
                msg += 'PLC: {}\n'.format(b.get_board_type[board_id]['plc'])
                msg += 'Power On: {}\n'.format(b.get_board_type[board_id]['power_on'])
                msg += 'PWM: {}\n'.format(b.get_board_type[board_id]['pwm'])
                msg += 'RFID: {}\n'.format(b.get_board_type[board_id]['rfid'])
                msg += 'PRO: {}\n'.format(b.get_board_type[board_id]['protection'])

                Unit = self.devices['DeviceID2Unit']["{}-0".format(b.RXtrama[0])]
                Devices[Unit].Update(nValue=1, sValue=msg)
                
                # Devices[Unit].Update(nValue = 0, sValue = sValue)

            # print(b.RXtrama) # Non togliere altrimenti non funziona
            if len(b.RXtrama) > 1:  # ERA 1 Mosra solo comunicazioni valide (senza PING)
                # print("Trama arrivata:", b.RXtrama, b.int2hex(b.RXtrama))
                # if (b.RXtrama[1] & 0xDF) in b.code: # comando valido o feedback a comando valido

                # if b.RXtrama[1] & 0xDF == b.code['COMUNICA_IO']:  # COMUNICA_IO / Scrive valore USCITA
                if b.RXtrama[1] in [ b.code['COMUNICA_IO'], b.code['RFID'] ]:  # COMUNICA_IO / Scrive valore USCITA                    
                    # print("onMessage>>>", b.RXtrama)
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

            b.writeLog()

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
