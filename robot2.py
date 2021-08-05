import socketio
import time
import wget
import numpy as np

sio = socketio.Client()

map_number = 'map_1'
localisation = 'DVIC' # TODO needs to be in the databsse !


# sensor doit avoir une de ces valeurs[ 0, 1, 2 ,3]
global_sensor = {
    'sensors' : [3, 3, 3, 3, 3, 3, 3], 
    'stats' : {
        'volt' : "10",
        'heatCore' : "70",
        'esp32_A' : "ON",
        "esp32_B" : "OFF",
        "slam" : "WAITING",
        "speed" : "5",
        'timeUsed' : "10"
    },
    'infos' : {
        'status' : True,
        'name' : "MK2R2_1",
        'ip' : '172.21.72.168',
        'ping' : "30"
    },
    'position' : [50, 50]
}

@sio.event
def connect():
    print('connection established')

@sio.event
def disconnect():
    print('disconnected from server')

def check_map():
    sio.emit('check_map', data = {sio.get_sid() : [map_number, localisation]})

@sio.on('good')
def good_map():
    print('I have the good map ! What would you expect ?')

@sio.on('download')
def download_map(data):
    print(data)
    wget.download(data["link"], '/home/teddy/Documents/DEVO/API_DEVO/MAP/map.txt')

def send_position():
    position = np.random.rand(1,3)
    sio.emit('position', data = position.tolist())

def send_global_data():
    sensors = np.random.randint(4, size=(7))
    # global_sensor['sensors'] = sensors.tolist()
    # position = np.random.rand(1,3)
    sio.emit('global_data', data = sensors.tolist())


@sio.on('command_to_do')
def good_command(data):
    print('DATA: ', data)

@sio.on('position_to_reach')
def good_position(data):
    print('DATA: ', data)

@sio.on('received')
def received(data):
    print(data)


if __name__ == '__main__':
    sio.connect('http://localhost:5000')    
    # sio.connect('https://devo-api.herokuapp.com/:5000')
    print(sio.connected)

    while True:
        if (sio.connected):
            print("connected")
            sio.emit('robot', "MK2R2_2")
            send_global_data()

            time.sleep(1) 