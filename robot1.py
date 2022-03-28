import socketio
import time
import wget
import numpy as np
import base64
import cv2 
import pickle
import threading

sio = socketio.Client()

map_number = 1
localisation = 'DVIC'
start_Time = None



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
        'name' : "MK3_1",
        'ip' : '172.21.72.168',
        'ping' : "30"
    },
    'position' : [50, 50]
}


data_operator = {
    'name'     : "MK3_1",
    'latitude' : 48.898750,
    'longitude': 2.093590,
    # 'position' : {'lat' : 48.89518737792969, 'lng' : 2.128262758255005},
    'batterie' : '40%',
    'status'   : 'DELIVERY'
}




@sio.event
def connect():
    print('connection established')

@sio.event
def disconnect():
    print('disconnected from server')

@sio.on('good')
def good_map():
    print('I have the good map ! What would you expect ?')

@sio.on('pong')
def pong():
    print("Ping API", (time.time() - start_Time) * 1000)

@sio.on('download')
def download_map(data):
    # print(data['image_data'])
    print('download')
    # print(data['session_data'])

    # im_bytes = base64.b64decode(data['image_data'])
    # im_arr = np.frombuffer(im_bytes, dtype=np.uint8)  # im_arr is one-dim Numpy array
    # img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)

    # cv2.imwrite("MAP/image.png", img)

    # image_64_decode = base64.decodebytes(data['session_data'])
    # print(image_64_decode)

    # print(data['image_data'])
    # print(data['session_data'])
    # wget.download(data["link_png"], '/home/teddy/Documents/DEVO/API_TEST/Mine_API_TEST/MAP/map.png')

@sio.on('command_to_do')
def good_command(data):
    print('DATA: ', data)

@sio.on('position_to_reach')
def good_position(data):
    print('DATA: ', data)

@sio.on('received')
def received(data):
    print(data)

@sio.on('operator_order_command')
def order_command(data):
    print(data)

@sio.on('operator_order_controller')
def order_controller(data):
    print(data)
    





def send_position():
    position = np.random.rand(1,3)
    sio.emit('position', data = position.tolist())

def send_global_data():
    sensors = np.random.randint(4, size=(7))
    # global_sensor['sensors'] = sensors.tolist()
    # position = np.random.rand(1,3)
    sio.emit('global_data', data = sensors.tolist())

def check_map():
    sio.emit('check_map', data = {"map_id" : map_number, "localisation": localisation})

def video_stream():
    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160);
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120);
    i = 0

    while True:    
        ret, photo = cap.read()    
        
        # cv2.imshow('streaming', photo)    
        
        # ret, buffer = cv2.imencode(".jpg", photo, [int(cv2.IMWRITE_JPEG_QUALITY),30])    

        # data_encode = np.array(buffer)
        # byte_encode = data_encode.tobytes()
        # x_as_bytes = pickle.dumps(buffer)

        if i % 1 == 0:
            ret, buffer = cv2.imencode('.jpg', photo)
            jpg_as_text = base64.b64encode(buffer)
            jpg_as_text = f"data:image/jpg;base64, {str(jpg_as_text)[2:-1]}"
            # print(jpg_as_text)
        
            sio.emit('stream_video', jpg_as_text)
        
        if cv2.waitKey(10) == 13:
            break  

        i += 1
        


if __name__ == '__main__':
    connected = False
    map_check = False
    while not connected:
        try:
            # sio.connect('http://0.0.0.0:5000')    
            sio.connect('http://api-devo-docker.herokuapp.com/')
        except socketio.exceptions.ConnectionError as err:
            print("ConnectionError: ", err)
        else:
            threading.Thread(target=video_stream).start()
            print("Connected!")
            connected = True
            sio.emit('robot', "MK3_1")
            sio.emit('robot_status_operator', data_operator)

            i = 0
            while True:
                # send_global_data()
                start_Time = time.time()
                sio.emit('ping')
                sio.emit('robot_data_operator', data_operator)

                if not map_check:
                    check_map()
                    map_check = True

                i += 1
                time.sleep(1) 