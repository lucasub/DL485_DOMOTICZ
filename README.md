# ITALIANO

# Domocontrol DL485 - Plugin per Domoticz
Plugin in Python3 per Domoticz che permette la gestione e il controllo delle board per domotica della serie DL485x

<div>
    <img src="document/image/DL485P.png" width="22%" style="float:left;" />
    <img src="document/image/DL485M.png" width="22%" style="float:left;" />
    <img src="document/image/DL485B.png" width="22%" style="float:left;" />
    <img src="document/image/DL485R.png" width="22%" style="float:left;" />
</div>

## Installazione 

1. Aggiornare e Installare i seguenti pacchetti da terminale:
```
sudo apt update
sudo apt upgrade
sudo apt install python3-dev python3-serial git python3-pip
```

2. Installare la libreria DL485_BUS
```
cd ~
git clone https://github.com/lucasub/DL485_BUS.git DL485_BUS
```

3. Entrare su DL485_BUS tramite il comando ed installare tutte le dipendenze
```
cd DL485_BUS
sudo pip3 install -r requirements.txt
```

4. Modificare il file di configurazione config.json secondo le proprie esigenze
```
nano config.json
```

3. Clonare il plugin dentro l'apposita cartella Domoticz ed installare le dipendenze
```
cd /home/pi/domoticz/plugins
git clone https://github.com/lucasub/DL485_DOMOTICZ.git DL485_DOMOTICZ
sudo pip3 install -r requirements.txt
```
4. Riavviare domoticz tramite Configurazione->Più opzioni->Riavvia il sistema

5. Dal menu "Configurazione->Hardware" selezionare il plugin "DL board plaugin" dalla tendina Modello
<img src="document/image/DL485_DOMOTICZ_A.png" width="1000px" style="float:left;" />

6. Dare un nome al plugin tramite la casella di testo "Nome" e aggiungerlo tramite il tasto "Aggiungi"
<img src="document/image/DL485_DOMOTICZ_B.png" width="1000px" style="float:left;" />

7. Il Plugin creerà tutti i dispositivi come da file di configurazione config.json presente nella cartella /home/pi/DL485_BUS

8. Nel caso vengano fatte delle modifiche al file config.json, è possibile aggiornare la configurazione di Domoticz semplicemente premendo il tasto Aggiorna dopo aver selezionato il plugin dalla lista dei plugin attivi

## Aggiornamento Plugin

1. Andare nella cartella del plugin
```
cd /home/pi/domoticz/plugins/DL485_DOMOTICZ
git pull
```
2. Riavviare domoticz oppure aggiornare il plugin dalla lista dei plugin installati

## Informazioni

Per tutte le informazioni sulle funzionalità e configurazione delle Board DL485: https://www.domocontrol.info

---

# ENGLISH

# Domocontrol DL485 - Domoticz Python Plugin
Python3 plugin for Domoticz to add integration with dl485_domoticz project

## Installation

1. Clone repository into your domoticz plugins folder
```
cd /home/pi/domoticz/plugins
git clone https://github.com/lucasub/DL485_DOMOTICZ.git DL485_DOMOTICZ
```
2. Restart domoticz
3. Make sure that "Accept new Hardware Devices" is enabled in Domoticz settings
4. Go to "Setup->Hardware" page and add new item with type "DL Board plugin - SERIAL"
5. Press Add button

## Plugin update

1. Go to plugin folder and pull new version
```
cd /home/pi/domoticz/plugins/DL485_DOMOTICZ
git pull
```
2. Restart domoticz

## Informations

For all informations about configurations: https://www.domocontrol.info
