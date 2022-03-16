import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import numpy as np
import time
from datetime import date

cred = credentials.Certificate('hive-delivery-firebase.json')
firebase_admin.initialize_app(cred)

db = firestore.client()





def get_orders():
    # READ DATA FROM FIRESTORE
    docs = db.collection('orders').order_by('timestamp').get()

    for doc in docs:
        print(doc.to_dict())
        print()

    print()
    print()


if __name__ == '__main__':

    # while True:

        get_orders()

        # time.sleep(5)


