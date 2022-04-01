import firebase_admin
import numpy as np
import sqlite3
import asyncio
import threading

# import eventlet
# eventlet.monkey_patch()

######################### OLD VERSION TO IMPROVE #########################


import time
from datetime import date
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import firestore
from flask import Flask, Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash


socketio = SocketIO(cors_allowed_origins='*')
db = SQLAlchemy()
DB_NAME = "users.db"


cred = credentials.Certificate('FIREBASE/hive-delivery-firebase.json')
firebase_admin.initialize_app(cred)

db_firestore = firestore.client()


##########################################################################################

#region GLOBAL VARIALBLE

robot                = {}
interface            = {}
operator             = {}
dictionnary_position = {}
download_dict        = {}
robotData_operator   = {}

# FIREBASE PARAM
date_dict            = {}
map_1                = {}
position_dict        = {}
today                = str(date.today())
date_dict[today]     = {}
    
link_interface       = {}

# sensor doit avoir une de ces valeurs[ 0, 1, 2 ,3]
global_sensor = {
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
    'position' : [50, 50],
    'projection' : [0,0],
    'lidar_data': [[0, 0.5], [0, 1]]
}

debug_sensor = {
    'keypoint_path' : [[0, 0], [10, 10]],
    'target_keypoint' : [0, 0]
}

global_sensor_empty = {
    'sensors' : [0, 0, 0, 0, 0, 0, 0], 
    'stats' : {
        'volt' : "0",
        'heatCore' : "0",
        'esp32_A' : "OFF",
        "esp32_B" : "OFF",
        "slam" : "OFF",
        "speed" : "0",
        'timeUsed' : "0"
    },
    'infos' : {
        'status' : False,
        'name' : "MK2R2_1",
        'ip' : '172.21.72.168',
        'ping' : "0"
    },
    'position' : [0, 0]
}

#endregion

##########################################################################################




#region DATABASE 

# SQL PARAM
map_database             = "map_sqlite.db"
robot_database           = "robots_sqlite.db"
position_target_database = "position_targets.db"

# SQL FUNCTIONS
def db_map_connection():
    conn_map = None
    try:
        conn_map = sqlite3.connect(map_database, check_same_thread=False)
    except sqlite3.Error as e:
        print(e)
    return conn_map

def db_robot_connection():
    conn_robot = None
    try:
        conn_robot = sqlite3.connect(robot_database, check_same_thread=False)
    except sqlite3.Error as e:
        print(e)
    return conn_robot

def db_position_connection():
    conn_position = None
    try:
        conn_position = sqlite3.connect(position_target_database, check_same_thread=False)
    except sqlite3.Error as e:
        print(e)
    return conn_position

conn_map = db_map_connection()
cur_map = conn_map.cursor()

conn_robot = db_robot_connection()
cur_robot = conn_robot.cursor()

conn_position = db_position_connection()
cur_position = conn_position.cursor()

#endregion



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = "helloworld"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


socketio.init_app(app)










@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get("email")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        email_exists = User.query.filter_by(email=email).first()
        username_exists = User.query.filter_by(username=username).first()

        if email_exists:
            flash('Email is already in use.', category='error')
        elif username_exists:
            flash('Username is already in use.', category='error')
        elif password1 != password2:
            flash('Password don\'t match!', category='error')
        elif len(username) < 2:
            flash('Username is too short.', category='error')
        elif len(password1) < 6:
            flash('Password is too short.', category='error')
        elif len(email) < 4:
            flash("Email is invalid.", category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('User created!')
            return redirect(url_for('home'))

    return render_template("signup.html", user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))











@app.route("/")
@app.route('/api', methods=['GET'])
@login_required
def home():
    if request.method == 'GET':
        cursor_OFF = cur_robot.execute("SELECT name FROM robots WHERE connection='OFF' AND localisation='{}'".format(current_user.username))
        rows_OFF   = cursor_OFF.fetchall()

        cursor_ON  = cur_robot.execute("SELECT name FROM robots WHERE connection='ON' AND localisation='{}'".format(current_user.username))
        rows_ON    = cursor_ON.fetchall()

        robot_OFF = []
        robot_ON = []

        for row in rows_OFF:
            robot_OFF.append(row[0])

        for row in rows_ON:
            robot_ON.append(row[0])


        return render_template("home.html", user=current_user, robot_ON=robot_ON, robot_OFF=robot_OFF, link=link_interface)

@app.route('/api/robot', methods=['GET', 'POST'])
@login_required
def all_robot():
    if request.method == 'GET':
        cursor = cur_robot.execute("SELECT * FROM robots WHERE localisation='{}'".format(current_user.username))

        robots = [
            dict(id=row[0], name=row[1], status=row[2], connection=row[3], localisation=row[4], map=row[5])
            for row in cursor.fetchall()
        ]

        if robots is not None:
            return jsonify(robots)
    
    if request.method == 'POST':
        new_id = request.form['id']
        new_name = request.form['name']
        new_status = request.form['status']
        new_connection = request.form['connection']

        sql = """INSERT INTO robots (id, name, status, connection)
                VALUES (?, ?, ?, ?)"""

        cursor = cur_robot.execute(sql, (new_id, new_name, new_status, new_connection))
        conn_robot.commit()

        return f"Robot with the id: {cursor.lastrowid} created successfully"

@app.route('/api/robot/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def one_robot(id):
    if request.method == 'GET':
        robot = None
        cursor = cur_robot.execute("SELECT * FROM robots WHERE ID={} AND localisation='{}'".format(id, current_user.username))
        rows = cursor.fetchall()

        robot = []

        for r in rows:
            robot.append(r)
       
        print(robot)

        if not robot:
            abort(404, message="Something wrong")
        else:
            return jsonify(robot), 200

    if request.method == 'PUT':
        sql = """ UPDATE robots 
                SET name=?, 
                    status=?,
                    connection=?
                WHERE id=? """
         
        name = request.form['name']
        status = request.form['status']
        connection = request.form['connection']


        updated_robot = {
            "id": id,
            "name": name,
            "status": status,
            "connection": connection
        }

        conn_robot.execute(sql, (name, status, connection, id))
        conn_robot.commit()
        return jsonify(updated_robot)

    if request.method == 'DELETE':
        sql = """ DELETE FROM robots WHERE id=? """
        conn_robot.execute(sql, (id,))
        conn_robot.commit()

        return "The robot with id: {} has been deleted".format(id), 200
    
@app.route('/api/map/meta', methods=['GET', 'POST'])
@login_required
def all_map():
    if request.method == 'GET':
        cursor = cur_map.execute("SELECT * FROM map WHERE Place='{}'".format(current_user.username))

        maps = [
            dict(place=row[0], name=row[1])
            for row in cursor.fetchall()
        ]

        if maps is not None:
            return jsonify(maps)
    
    if request.method == 'POST':
        new_place = request.form['Place']
        new_map_name = request.form['Map_name']

        sql = """INSERT INTO map (place, map_name)
                VALUES (?, ?)"""

        cursor = cur_map.execute(sql, (new_place, new_map_name))
        conn_map.commit()

        return f"Map with the id: {cursor.lastrowid} created successfully"

################################################

# TODO ADD LOGIN_REQUIRED POUR LES ROBOTS

@app.route('/api/map/download/map.session', methods=['GET', 'POST'])
# @login_required
def map_session():
    with open('map.session', 'rb') as f:
        session_data = f.read()
    session_data = bytearray(session_data)
    return session_data

@app.route('/api/map/download/map.png', methods=['GET', 'POST'])
# @login_required
def map_png():
    with open('map.png', 'rb') as f:
        image_data = f.read()
    image_data = bytearray(image_data)
    return image_data

################################################

@app.route('/api/position_target', methods=['GET'])
@login_required
def all_position():
    if request.method == 'GET':
        cursor = cur_position.execute("SELECT * FROM position_target")

        maps = [
            dict(place=row[0], i=row[1], j=row[2])
            for row in cursor.fetchall()
        ]

        if maps is not None:
            return jsonify(maps)

@app.route('/api/robot/<name>/manual/<command>', methods=['GET'])
def robot_command(name, command):
    if request.method == 'GET':
        print(robot)
        sid = robot[str(name)]
        data = "SID: " + sid + " have to do this command : " + command
        
        socketio.emit('command_to_do', command, to=sid)
        
        return data

@app.route('/api/robot/<name>/position/<position>', methods=['GET'])
def robot_position_to_reach(name, position):
    if request.method == 'GET':
        sid = robot[str(name)]
        data = "SID: " + sid + " have to go there : " + position

        position = "'" + position + "'"

        cursor = cur_position.execute("SELECT * FROM position_target WHERE name={}".format(position))

        maps = [
            dict(place=row[0], i=row[1], j=row[2])
            for row in cursor.fetchall()
        ]

        if maps is not None:
            print(maps)          

        dictionnary_position['i'] = maps[0]["i"]
        dictionnary_position['j'] = maps[0]["j"]

        socketio.emit('position_to_reach', dictionnary_position, to=sid)

        return data












@socketio.on('connect')
def test_connect():
    print('Client Connected')

# TODO EMIT ping and receive pong to calculate in the api not in the robot  
@socketio.on('ping')
def ping():
    username = request.sid
    socketio.emit('pong', to=username)









@socketio.on('robot')
def handle_message(auth):
    print(auth, 'Connected')
    username = request.sid
    room = request.sid
    join_room(room)

    robot[auth] = username
        
    sql = """ UPDATE robots 
            SET connection=?
            WHERE name=? """

    connection = "ON"

    conn_robot.execute(sql, (connection, auth))
    conn_robot.commit()

    # cursor = cur_robot.execute("SELECT * FROM robots")

    # robots = [
    #     dict(id=row[0], name=row[1], status=row[2], connection=row[3], localisation=row[4], map=row[5])
    #     for row in cursor.fetchall()
    # ]

    # print('ROBOTS : ', list(robots))

    position_dict[auth] = []

    link_interface[auth] = 'http://localhost:8080/#/' + str(auth)

    socketio.emit('received', "ok", to=username)
    # print(operator['123'])
    # socketio.emit('operator_data', list(robots), to=operator['123'])








@socketio.on('interface')
def handle_message_interface(auth):
    global interface

    print(auth, ' Interface Connected')
    username = request.sid
    room = request.sid
    join_room(room)
    
    interface[auth] = username

    filepath = 'map.png'

    im=Image.open(filepath)

    with open('map.png', 'rb') as f:
        image_data = f.read()
    
    socketio.emit('received_image', {'image_data': image_data}, to=username)
    socketio.emit('size_map', im.size, to=username)







# CONNECTION FROM THE OPERATOR DATABASE, SEND BACK STATUS OF EVERY ROBOT LIVE FROM DATABASE
@socketio.on('operator_interface')
def handle_message_interface(auth):
    global operator, robot

    print(auth, ' : Operator Interface Connected')
    username = request.sid
    room = request.sid
    join_room(room)
    
    operator[auth] = username

    cursor = cur_robot.execute("SELECT * FROM robots")

    robots = [
        dict(id=row[0], name=row[1], status=row[2], connection=row[3], localisation=row[4], map=row[5])
        for row in cursor.fetchall()
    ]

    socketio.emit('operator_data', list(robots), to=username)


# UPDATE STATUS OF THE ROBOT IN THE DATABASE AND SEND TO OPERATOR INTERFACE
@socketio.on('robot_status_operator')
def handle_status_operator(data):

    auth = data['name']

    sql = """ UPDATE robots 
            SET status=?
            WHERE name=? """

    status = data['status']

    conn_robot.execute(sql, (status, auth))
    conn_robot.commit()

    cursor = cur_robot.execute("SELECT * FROM robots")

    robots = [
        dict(id=row[0], name=row[1], status=row[2], connection=row[3], localisation=row[4], map=row[5])
        for row in cursor.fetchall()
    ]

    sid = operator['123']
    socketio.emit('operator_data', list(robots), to=sid)



# SHARE DATA WITH THE OPERATOR THAT CAN CHANGE OFTEN, NEARLY LIVE DATA (position, battery; etc...)
@socketio.on('robot_data_operator')
def handle_data_operator(data):
    global robotData_operator
    data['position'] = {'lat' : data['latitude'], 'lng': data['longitude']}  
    del data['latitude']
    del data['longitude']
    shared_received = data

    robotData_operator[data['name']] = shared_received
    # print(robotData_operator)

    if bool(operator):
        sid = operator['123']
        socketio.emit('MESSAGE_operator', robotData_operator, to=sid)

@socketio.on('operator_command')
def handle_command_operator(data):
    shared_received = data

    if bool(operator):
        sid = robot[shared_received[0]]
        socketio.emit('operator_order_command', shared_received[1], to=sid)


@socketio.on('operator_command_controller')
def handle_controller_operator(data):
    shared_received = data

    if bool(operator):
        sid = robot[shared_received[0]]
        socketio.emit('operator_order_controller', shared_received, to=sid)

# Receive Video Stream from robot and send it back to Operator
@socketio.on('stream_video')
def stream_video(data):

    if bool(operator):
        sid = operator['123']
        socketio.emit('streamVideo', data, to=sid)

@socketio.on('stream_lidar')
def stream_lidar(data):

    if bool(operator):
        sid = operator['123']
        socketio.emit('streamLidar', data, to=sid)

@socketio.on('stream_active')
def stream_active(data):

    if bool(operator):
        sid = sid = robot[data[0]]
        socketio.emit('stream_ON', data[1], to=sid)
    







@socketio.on('global_data')
def handle_global_data(data):
    shared_received = data

    # sensors     = [shared_received['ulF1'], shared_received['ulF0'], shared_received['ulF3'], shared_received['ulF2'], shared_received['ulB0'], shared_received['ulB1'], shared_received['ulB2']]
    # sensors     = [1 if x >= 2000 else 3 if x < 500 else 2 for x in sensors]
    volt        = str(shared_received['voltage'])
    heatCore    = str(shared_received['cpu_heat'])
    if shared_received['microA_state'] == 1:
        esp32_A     = "ON"
    else:
        esp32_A     = "OFF"
    if shared_received['microB_state'] == 1:
        esp32_B     = "ON"
    else:
        esp32_B     = "OFF"
    slam            = str(shared_received['slam_state'])
    speed           = "TODO"
    timeUsed        = "TODO"
    ping            = "TODO"
    
    position_i      = str(shared_received['pose_ti'])
    position_j      = str(shared_received['pose_tj'])
    position        = [position_i, position_j]

    projection_i    = str(shared_received['pose_vi'])
    projection_j    = str(shared_received['pose_vj'])
    projection      = [projection_i, projection_j]

    lidar_data      = str(shared_received['lidar_data'])



    # global_sensor['sensors']            = sensors
    global_sensor['stats']['volt']      = volt
    global_sensor['stats']['heatCore']  = heatCore
    global_sensor['stats']['esp32_A']   = esp32_A
    global_sensor['stats']['esp32_B']   = esp32_B
    global_sensor['stats']['slam']      = slam
    global_sensor['stats']['speed']     = speed
    global_sensor['stats']['timeUsed']  = timeUsed
    global_sensor['infos']['ping']      = ping
    global_sensor['position']           = position
    global_sensor['projection']         = projection
    
    global_sensor['lidar_data']         = lidar_data

    if bool(interface):
        for key, value in list(robot.items()):
            if value == request.sid:
                name = key
        
        sid = interface[name]
        socketio.emit('MESSAGE', global_sensor, to=sid)
        print("emitted")


@socketio.on('data_debug_robot')
def handle_debug_data(data):
    shared_received = data
    
    path                                    = str(shared_received['keypoint_path'])
    target_keypoints_x                      = str(shared_received['target_keypoints_x'])
    target_keypoints_y                      = str(shared_received['target_keypoints_y'])

    target_keypoint                         = [target_keypoints_x, target_keypoints_y]

    debug_sensor['keypoint_path']           = path
    debug_sensor['target_keypoint']         = target_keypoint

    if bool(interface):
        for key, value in list(robot.items()):
            if value == request.sid:
                name = key
        
        sid = interface[name]
        socketio.emit('MESSAGE_debug', debug_sensor, to=sid)
        print("emitted")

@socketio.on('check_map')
def handle_message(data):
    print("Processing Map Checking...")

    map_number = data["map_id"]
    place = data["localisation"]

    if map_number == get_data(data):
        print("Good emitted")
        socketio.emit('good', to=request.sid)
    else:
        print("Download emitted")

        place = "'" + place + "'"
        cursor = cur_map.execute("SELECT * FROM map WHERE place={}".format(place))

        maps = [
            dict(place=row[0], map_name=row[1])
            for row in cursor.fetchall()
        ]

        if maps is not None:
            print(maps)          

        download_dict["id"]           = maps[0]["map_name"]
        download_dict["localisation"] = maps[0]["place"]
        download_dict["link_session"] = "https://api-devo-docker.herokuapp.com/api/map/download/map.session"
        download_dict["link_png"]     = "https://api-devo-docker.herokuapp.com/api/map/download/map.png"
        # download_dict["link_png"]     = "http://0.0.0.0:5000/api/map/download/map.png"

        socketio.emit('download', download_dict, to=request.sid)

################################################

#region TODO REVERIFIER POSITION
# @socketio.on('position')
# def handle_message(data):
#     position = np.empty(2)
#     position[0] = data["i"]
#     position[1] = data["j"]

#     robot_map = data["localisation"]

#     robot_name = None

#     for key, value in list(robot.items()):
#         if value == request.sid:
#             robot_name = key

#     if robot_name in position_dict:
#         position_dict[robot_name].append(list(position))
#     else :
#         position_dict[robot_name] = list(position)


#     position_dict_of_robot = position_dict[robot_name]
#     robot_data = {robot_name : position_dict_of_robot}


#     date_dict[today][robot_map] = robot_data

#     # THANKS TO THE SID, add to FIREBASE the postion of the robot with the good SID
#     print("DICTIONNARY SENT : ", date_dict)

#     # TODO NOT WORKING check connection first maybe ?? 
#     ref = db.reference('/')
#     ref.set(date_dict)

#endregion

################################################








@socketio.on('disconnect')
def disconnect():

    room = request.sid
    leave_room(room)
    print("Client leave room:" + request.sid)

    close_room(room)
    print("Room: ", room, " is closed.")
    
    name_robot = None
    name_interface = None
    # If robot disconnects: request.sid with be the sid of the robot
    for key, value in list(robot.items()):
        if value == request.sid:
            name_robot = key
            del robotData_operator[key]
            del robot[key]
            del link_interface[key]
            print(key, "is deleted")
            if bool(interface) and name_robot in interface:
                socketio.emit('MESSAGE', global_sensor_empty, to=interface[name_robot])

    sql = """ UPDATE robots 
            SET connection=?
            WHERE name=? """

    connection = "OFF"

    conn_robot.execute(sql, (connection, name_robot))
    conn_robot.commit()

    sql = """ UPDATE robots 
            SET status=?
            WHERE name=? """

    status = 'STOP'

    conn_robot.execute(sql, (status, name_robot))
    conn_robot.commit()


    cursor = cur_robot.execute("SELECT * FROM robots")

    robots = [
        dict(id=row[0], name=row[1], status=row[2], connection=row[3], localisation=row[4], map=row[5])
        for row in cursor.fetchall()
    ]

    # print(robots)
    boolDataBase = False
    for r in robots:
        if r['connection'] == 'ON':
            boolDataBase = True

    if boolDataBase == False:
        socketio.emit('MESSAGE_operator', {}, to=operator['123'])

    if operator:
        socketio.emit('operator_data', list(robots), to=operator['123'])

    # If interface disconnects: request.sid with be the sid of the interface
    for key, value in list(interface.items()):
        if value == request.sid:
            name_interface = key
            del interface[key]

    print('Client disconnected')









def get_data(data):
    # GOAL : return the SQL map name corresponding to the location of the robot 
    print("Data from check_map(): ", data)

    cursor = cur_map.execute("SELECT * FROM map")

    maps = [
        dict(place=row[0], name=row[1])
        for row in cursor.fetchall()
    ]

    for dict_ele in maps:
        if dict_ele['place'] == data["localisation"]:
            result = dict_ele['name']

    # Result is the name of the map which share the sme localisation a the data from the robot 
    return result

# @socketio.on('firebase_socket')
def get_orders():
        # print('OK')
        # docs = db_firestore.collection('orders').get()
        # print(docs)
        # for doc in docs:
        #     print(doc.to_dict())
        #     print()

    while True:
        # READ DATA FROM FIRESTORE
        docs = db_firestore.collection('orders').order_by('timestamp').get()
        print("docs ", docs)
        # print(docs)
        for doc in docs:
            print(doc.to_dict())
            print()

        time.sleep(5)

# threading.Thread(target=get_orders).start()
# eventlet.spawn(get_orders)

if __name__ == '__main__':
    # socketio.run(app, host="0.0.0.0")
    # input()
    # TODO CHANGE THIS TO RUN HEROKU
    app.run(host="0.0.0.0")