import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import numpy as np
import time
from datetime import date

cred = credentials.Certificate('mk2r2-firebase.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mk2r2-firebase-default-rtdb.europe-west1.firebasedatabase.app/'
})


def get_position(dict, today):
    position_robot1 = np.random.rand(1,3)
    position_list_robot1 = position_robot1.tolist()

    position_robot2 = np.random.rand(1,3)
    position_list_robot2 = position_robot2.tolist()
    
    dict[today]["Map_1"]["MK2R2_1"].extend(position_list_robot1)
    dict[today]["Map_1"]["MK2R2_2"].extend(position_list_robot2)
    # print(dict)

    ref = db.reference('/')

    ref.set(dict)
    
if __name__ == '__main__':
    today = str(date.today())

    date_dict = {}
    map_1 = {}
    position_dict = {}
    
    date_dict[today] = {}

    position_dict['MK2R2_1'] = []
    position_dict['MK2R2_2'] = []

    map_1["Map_1"] = position_dict
    date_dict[today] = map_1 

    # print(date_dict)

    while True:
        # position = np.random.rand(1,3)
        # position_list = position.tolist()
        
        # map_1["Map_1"]["MK2R2_1"].extend(position_list)
        # print(map_1)

        get_position(date_dict, today)
        print("Added")

        time.sleep(2)

