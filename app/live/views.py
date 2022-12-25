from flask import render_template
from flask_socketio import emit, join_room, leave_room, \
    close_room
from flask_login import current_user
import time
from random import randint

from . import live
from app import socketio, db
from app.models import Message
from _3rdparty import RtcTokenBuilder, Role_Attendee


APP_ID = "9bc67c8ada924e3791eab763ea5d97e5"
APP_CERTIFICATE = "5dafe8c0db13417f93edbafd03bc2b01"
CHANNEL_NAME = "live"
EXPIRE_TIME_IN_SECONDS = 3600


# View Functions
@live.route('/admin_live', methods=['POST', 'GET'])
def admin_live():
    return render_template('admin/live.html')


# Basic Operations
@socketio.on('join', namespace='/liveroom')
def join(message):
    join_room("liveroom")
    emit('join_response', message, room="liveroom")


@socketio.on('leave', namespace='/liveroom')
def leave(message):
    leave_room("liveroom")
    emit('leave_response', message, room="liveroom")


@socketio.on('close', namespace='/liveroom')
def close(message):
    close_room("liveroom")


@socketio.on('send', namespace='/liveroom')
def send(message):
    emit('msg_response', message, room="liveroom")


@socketio.on('request_token', namespace='/liveroom')
def request_token(message):
    uid = current_user.id
    # uid = randint(1, 1000)  # when test on the same device
    current_time = int(time.time())
    expire_time = current_time + EXPIRE_TIME_IN_SECONDS
    token = RtcTokenBuilder.buildTokenWithUid(
        APP_ID, APP_CERTIFICATE, CHANNEL_NAME, uid, Role_Attendee, expire_time)
    emit("token_response", {
            "token": token,
            "appid": APP_ID,
            "channel": "live",
            "uid": uid,
            "user": current_user.username}, room="liveroom")
