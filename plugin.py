"""
<plugin key="DLBOARD" name="DL Board plugin - SERIAL" author="Luca Subiaco e Daniele Gava" version="1.0.0" externallink="https://www.dmocontrol.info/" wikilink="https://www.domocontrol.info">
	<params>
        <param field="SerialPort" label="Serial Port" width="200px" required="true"/>

        <param field="Mode3" label="Speed RS485" width="150px">
            <options>
                <option label="1200" value=1200/>
                <option label="2400" value=2400/>
                <option label="4800" value=4800/>
                <option label="9600" value=9600   default="true"/>
                <option label="14400" value=14400/>
                <option label="19200" value=19200/>
                <option label="28800" value=28800/>
                <option label="38400" value=38400/>
                <option label="57600" value=57600/>
                <option label="115200" value=115200/>
        	</options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
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
import dl485

print("-" * 50, "Begin DL485-Serial plugin", "-" * 50, end="\n")
b = dl485.Bus()  # Istanza la classe Bus
l = dl485.Log()
config_file_name = "/home/pi/domoticz/plugins/DL485_DOMOTICZ/config.json"  # File di configurazione
b.getJsonConfig(config_file_name)
b.BOARD_ADDRESS = int(b.config['GENERAL']['board_address'])

# Configurazione SCHEDE
msg = b.resetEE(1, 0)  # Board_id, io_logic. Se io_logic=0, resetta tutti gli IO
# print(msg)
# self.TXmsg += msg
b.dictBoardIo()  # Crea il DICT con i valori IO basato sul file di configurazione (solo board attive)

""" LOOP """
class BasePlugin:
    def __init__(self):
        self.debug = 0
        self.RXtrama = []
        self.TXmsg = []  # Lista che contiene le liste da trasmettere sul BUS
        self.BOARD_ADDRESS = b.BOARD_ADDRESS
        self.nowtime = 0
        self.board_ready = {}
        self.oldtime = time.time() - 10  # init self.oldtime per stampe dizionario con i/o per stampa subito al primo loop
        self.mapUnit2DeviceID = {}
        configuration = b.sendConfiguration()  # Set configuration of boards
        # print("Configuration:", configuration)
        self.TXmsg = configuration

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

        Unit = 0

        for board_id in b.mapiotype:
            for io_logic in b.mapiotype[board_id]:
                Unit += 1
                DeviceID = "%s-%s" % (board_id, io_logic)
                self.mapUnit2DeviceID[Unit] = DeviceID
                self.mapUnit2DeviceID[DeviceID] = Unit
                name = "%s %s" % (DeviceID, b.mapiotype[board_id][io_logic]['name'])
                description = b.mapiotype[board_id][io_logic]['description']
                dtype = b.mapiotype[board_id][io_logic]['dtype']

                # Create new device on Domoticz
                if not Unit in Devices:
                    Domoticz.Device(Name=name, Unit=Unit, TypeName=dtype, Description=description, DeviceID=DeviceID ,Used=1 ).Create()

                # Update device on Domoticz
                value = int(b.mapiotype[board_id][io_logic]['default_startup_value']) if 'default_startup_value' in b.mapiotype[board_id][io_logic] else 0
                sValue = 'On' if value else 'Off'

                if dtype == 'switch':
                    pass
                elif dtype == 'Temp+Hum':
                    sValue = "0;0;0"
                elif dtype == 'Temp+Hum+Baro':
                    sValue = "0;0;0;0;0"

                Devices[Unit].Update(Name = name, TypeName = dtype, Description = description,
                                     Used = 1, nValue = value, sValue = sValue )

        self.SerialConn = Domoticz.Connection(Name="DL485", Transport="Serial", Address = Parameters["SerialPort"], Baud = int(Parameters["Mode3"]))
        self.SerialConn.Connect()

    def onStop(self):
        Domoticz.Log("%s %s" % ("onStop DL485-SERIAL plugin", self))

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("%s %s %s %s %s" % ("onConnect DL485-SERIAL plugin", self, Connection, Status, Description))

    def onCommand(self, Unit, Command, Level, Hue):
        bio = Devices[Unit].DeviceID.split("-")
        board_id = int(bio[0])
        io_logic = int(bio[1])
        value = 1 if Command == 'On' else 0
        # value = b.make_inverted(board_id, io_logic, value)
        msg = b.writeIO(board_id, io_logic, [value])
        self.TXmsg.append(msg)

    def updateIO(self, board_id, io_logic, value):
        """
        Viene chiamata quando arriva una trama dalla rete per poter decodificare il messaggio e aggiornare lo stato di Domoticz
        """
        if not board_id in b.mapiotype or not io_logic in b.mapiotype[board_id]:
            return
        if not value:
            return

        DeviceID = '%s-%s' %(board_id, io_logic)
        Unit = self.mapUnit2DeviceID[DeviceID]
        dtype = b.mapiotype[board_id][io_logic]['dtype']

        if (Unit in Devices):
            # Domoticz.Debug("Device:{}, Board_id:{}, Io_logic:{}, value:{}".format(dtype, board_id, io_logic, value))
            if dtype == 'Switch':
                # b0: dato filtrato
                # b1: dato istantaneo
                # b2: fronte OFF
                # b3: fronte ON
                # b4: fronte OFF da trasmettere
                # b5: fronte ON da trasmettere

                x_value = value[0]
                value = value[0]
                # value = b.make_inverted(board_id, io_logic, value[0] & 1)  # Inverte l'IO se definito sul file di configurazione
                b.status[board_id]['io'][io_logic - 1] = value
                sValue = 'On' if value & 1 == 1 else 'Off'
                Devices[Unit].Update(value & 1, sValue)
                linked_proc = b.mapproc[DeviceID] if DeviceID in b.mapproc else {}
                
                plc_function = b.mapiotype[board_id][io_logic]['plc_function']

                if linked_proc and plc_function == 'disable':
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

                    # print("DeviceID:", DeviceID)
                    for x_out in linked_proc:
                        # print(x_out)
                        x_outa = x_out.split("-")
                        x_board_id = int(x_outa[0])
                        x_io_logic = int(x_outa[1])

                        app_linked_proc = linked_proc["%s-%s" %(x_outa[0], x_outa[1])]['linked_proc']
                        
                        if app_linked_proc == 'toggle':
                            if x_value & 0b100:
                                value = b.status[x_board_id]['io'][x_io_logic - 1]
                                value = 1 - value

                                value = b.make_inverted(x_board_id, x_io_logic, value)  # Inverte l'IO se definito sul file di configurazione
                                # print("TOGGLE", x_out, value)
                                msg = b.writeIO(x_board_id, x_io_logic, [value])
                                self.TXmsg.append(msg)

                        elif app_linked_proc == 'direct':
                            value = x_value & 1
                            value = b.make_inverted(x_board_id, x_io_logic, value)  # Inverte l'IO se definito sul file di configurazione
                            # print("DIRECT", x_out, value)
                            msg = b.writeIO(x_board_id, x_io_logic, [value])
                            self.TXmsg.append(msg)

                        elif app_linked_proc == 'invert':
                            value = (x_value & 1) ^ 1
                            value = b.make_inverted(x_board_id, x_io_logic, value)  # Inverte l'IO se definito sul file di configurazione
                            # print("INVERT", x_out, value)
                            msg = b.writeIO(x_board_id, x_io_logic, [value])
                            self.TXmsg.append(msg)
                        elif app_linked_proc == 'and':
                            linked_board_id_io_logic = b.mapiotype[x_board_id][x_io_logic]['linked_board_id_io_logic']
                            # print("linked_board_id_io_logic", linked_board_id_io_logic)
                            value = 1
                            for ii in linked_board_id_io_logic:
                                ii_outa = ii.split("-")
                                ii_board_id = int(ii_outa[0])
                                ii_io_logic = int(ii_outa[1])
                                value = value & b.status[ii_board_id]['io'][ii_io_logic - 1]
                            value = b.make_inverted(x_board_id, x_io_logic, value)  # Inverte l'IO se definito sul file di configurazione
                            msg = b.writeIO(x_board_id, x_io_logic, [value])
                            self.TXmsg.append(msg)

                        elif app_linked_proc == 'or':
                            linked_board_id_io_logic = b.mapiotype[x_board_id][x_io_logic]['linked_board_id_io_logic']
                            value = 0
                            for ii in linked_board_id_io_logic:
                                ii_outa = ii.split("-")
                                ii_board_id = int(ii_outa[0])
                                ii_io_logic = int(ii_outa[1])
                                value = value | b.status[ii_board_id]['io'][ii_io_logic - 1]
                            value = b.make_inverted(x_board_id, x_io_logic, value)  # Inverte l'IO se definito sul file di configurazione
                            msg = b.writeIO(x_board_id, x_io_logic, [value])
                            self.TXmsg.append(msg)
                        elif app_linked_proc == 'xor':
                            linked_board_id_io_logic = b.mapiotype[x_board_id][x_io_logic]['linked_board_id_io_logic']
                            value = 0
                            for ii in linked_board_id_io_logic:
                                ii_outa = ii.split("-")
                                ii_board_id = int(ii_outa[0])
                                ii_io_logic = int(ii_outa[1])
                                value = value ^ b.status[ii_board_id]['io'][ii_io_logic - 1]
                            value = b.make_inverted(x_board_id, x_io_logic, value)  # Inverte l'IO se definito sul file di configurazione
                            msg = b.writeIO(x_board_id, x_io_logic, [value])
                            self.TXmsg.append(msg)
                    
                    try:
                        Domoticz.Debug("Device:{}, Board_id:{}, Io_logic:{}, value:{}".format(dtype, board_id, io_logic, msg))
                    except:
                        print("ERROR send Devices dtype:{}, Board_id:{}, io_logic:{}".format(dtype, board_id, io_logic))

            elif dtype == 'Voltage':
                value = b.calculate(board_id, io_logic, value)
                sValue = str(value)
                b.status[board_id]['io'][io_logic - 1] = value
                b.voltageLimit(board_id, io_logic, value)  # Check and power down if limit voltage
                Devices[Unit].Update(nValue = int(value), sValue = sValue)
                Domoticz.Debug("Device:{}, Board_id:{}, Io_logic:{}, value:{}".format(dtype, board_id, io_logic, value))

            elif dtype == 'Temperature':
                value = b.calculate(board_id, io_logic, value)
                # print("temperature:", value)
                if value:
                    sValue = str(value)
                    # print("B:", value, sValue)
                    b.status[board_id]['io'][io_logic - 1] = value
                    Devices[Unit].Update(nValue = 0, sValue = sValue)
                    Domoticz.Debug("Device:{}, Board_id:{}, Io_logic:{}, value:{}".format(dtype, board_id, io_logic, value))

            elif dtype == 'Temp+Hum+Baro':
                value = b.calculate(board_id, io_logic, value)
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
                if value[2] < 1000: weather_prediction = 4
                elif value[2] < 1020: weather_prediction = 3
                elif value[2] < 1030: weather_prediction = 2
                else: weather_prediction = 1

                sValue = "{};{};{};{};{}".format(value[0], value[1], hum_stat, value[2], weather_prediction)
                # print("Unit in devices", dtype, Unit, sValue)
                b.status[board_id]['io'][io_logic - 1] = value
                Devices[Unit].Update(nValue=0, sValue=sValue)
                Domoticz.Debug("Device:{}, Board_id:{}, Io_logic:{}, value:{}".format(dtype, board_id, io_logic, value))
                
            elif dtype == 'Temp+Hum':
                value = b.calculate(board_id, io_logic, value)
                # print("TEMPERATURA AM2320", board_id, io_logic, value)

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
                b.status[board_id]['io'][io_logic - 1] = value
                Devices[Unit].Update(nValue=0, sValue=sValue)
                Domoticz.Debug("Device:{}, Board_id:{}, Io_logic:{}, value:{}".format(dtype, board_id, io_logic, value))

    def log(self, msg):
        """
        Print LOG if debuf==True
        """
        if self.debug:
            print("{} {:<30}".format(self.nowtime, msg))

    def onMessage(self, Connection, Data):
        self.nowtime = int(time.time())
        for d in Data:
            # print(d)
            self.RXtrama = b.readSerial(d)
            if self.RXtrama:
                # print(self.RXtrama)
                b.labinitric()  # Resetta la coda per nuova ricezione alla fine dei calcoli
                self.board_ready[self.RXtrama[0]] = self.nowtime  # Aggiorna la data di quando è stato ricevuto la trama del nodo
                
                if len(self.TXmsg):  # Controlla se c'è qualcosa da trasmettere

                    if self.BOARD_ADDRESS - 1 == self.RXtrama[0]:
                        msg = self.TXmsg.pop(0)
                        Domoticz.Log("TX on BUS: %s" %msg )
                        msg = b.eight2seven(msg)
                        msg = b.encodeMsgCalcCrcTx(msg)
                        Connection.Send(bytes(msg))

                if len(self.RXtrama) == 1:  # Mosra solo PING
                    pass
                    # print(self.RXtrama)

                if len(self.RXtrama) > 1:  # Mosra solo comunicazioni valide (senza PING)
                    if self.RXtrama[1] in b.code or (self.RXtrama[1] - 32) in b.code:
                        # print("-----------", self.RXtrama[1], code[self.RXtrama[1]])

                        if self.RXtrama[1] > 32:
                            self.RXtrama[1] = self.RXtrama[1] - 32
                            rtx = 'RX'
                        else:
                            rtx = 'TX'

                        if self.RXtrama[1] == 13 or self.RXtrama[1] - 32 == 13:  # Error message
                            # 5 byte:
                            # 1: IDBUS,
                            # 2: 29 16+13,
                            # 3: Comando che ha generato l'errore,
                            # 4: ID Logico associato al comando, codice errore
                            # 5: Tipo errore
                            err = '' if not self.RXtrama[4] in b.error else b.error[self.RXtrama[4]]
                            code = '' if not self.RXtrama[1] in b.code else b.code[self.RXtrama[1]]
                            msg = '{:<4} {:<20} {} {:<30} {}'.format(rtx, code, self.RXtrama, '', err)
                            self.log(msg)
                        else:
                            msg = '{:<4} {:<20} {}'.format(rtx, b.code[self.RXtrama[1]], self.RXtrama)
                            self.log(msg)

                        if self.RXtrama[1] == 14 or self.RXtrama[1] == 8:  # COMUNICA_IO / Scrive valore USCITA
                            self.updateIO(self.RXtrama[0], self.RXtrama[2], self.RXtrama[3:])  # Aggiorna DOMOTICZ

                    else:
                        if self.RXtrama[1] > 32:
                            self.RXtrama[1] = self.RXtrama[1] - 32
                            rtx = 'RX'
                        else:
                            rtx = 'TX'
                        msg = "{:<4} {:<20} {} {:<30} {}".format(rtx, '', self.RXtrama, '', 'ERRORE NON CODIFICATO')
                        self.log(msg)
                        Domoticz.Error("RXTRAMA - MSG NON CODIFICATO: {}".format(self.RXtrama))
                        

        # if self.debug and (self.nowtime - self.oldtime > 10):
        if (self.nowtime - self.oldtime > 10):
            self.TXmsg.append(b.ping())  # Not remove. Is neccesary to reset shutdown counter
            self.oldtime = self.nowtime

            # self.TXmsg.append(b.boardReboot(0))  # Reboot board
            # To send custom msg
            # print("SEND CUSTOM MESSAGE")
            # self.TXmsg.append(b.getTypeBoard(20))
            # self.TXmsg.append(b.getTypeBoard(20))
            # self.TXmsg.append(b.boardReboot(20))

            board_to_remove = []
            for k, v in self.board_ready.items():
                # print(v, nowtime-v, v)
                if (self.nowtime - v) > 5:
                    board_to_remove.append(k)
            for k in board_to_remove:
                del self.board_ready[k]

            msg = "     BOARD_READY          {:<17} ".format(str(list(self.board_ready.keys())))
            self.log(msg)
            b.printStatus()  # Print status of IO

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        pass
        # Domoticz.Log("%s %s %s %s %s %s %s %s %s %s %s" % (s, "onNotification", self, Name, Subject, Text, Status, Priority, Sound, ImageFile))
        # print("%s %s %s %s %s %s %s %s %s %s %s" % (s, "onNotification", self, Name, Subject, Text, Status, Priority, Sound, ImageFile))

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")
        # self.SerialConn = Close
        # Domoticz.Log("%s %s %s %s" % (s, "onDisconnect", self, Connection))
        # print("%s %s %s %s" % (s, "onDisconnect", self, Connection))
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
