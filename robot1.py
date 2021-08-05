import socketio
import time
import wget
import numpy as np
import base64
import cv2 

sio = socketio.Client()

map_number = 1
localisation = 'DVIC'


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
    sio.emit('check_map', data = {"map_id" : map_number, "localisation": localisation})

@sio.on('good')
def good_map():
    print('I have the good map ! What would you expect ?')

@sio.on('download')
def download_map(data):
    print(data['image_data'])
    im_bytes = base64.b64decode(data['image_data'])
    im_arr = np.frombuffer(im_bytes, dtype=np.uint8)  # im_arr is one-dim Numpy array
    img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)

    # cv2.imwrite("MAP/image.png", img)

    image_64_decode = base64.decodebytes(data['session_data'])
    # print(image_64_decode)

    # print(data['image_data'])
    # print(data['session_data'])
    # wget.download(data["link_png"], '/home/teddy/Documents/DEVO/API_TEST/Mine_API_TEST/MAP/map.png')

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
    # sio.connect('http://localhost:5000')    
    sio.connect('https://api-devo.herokuapp.com/:5000')
    print(sio.connected)

    i = 0
    while True:
        if (sio.connected):
            print("connected")
            sio.emit('robot', "MK2R2_1")
            send_global_data()

            if i%5 == 0:
                check_map()

            i += 1
            time.sleep(1) 