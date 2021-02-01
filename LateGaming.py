from dns import exception
from _socket import gaierror
from sounddevice import Stream as sound_Stream, sleep as sound_sleep
from numpy import linalg as np
from psutil import process_iter as running_processes, NoSuchProcess, ZombieProcess, AccessDenied
import time as tm
import pymongo as pm
from ntplib import NTPClient, NTPException
from os import system
from pymongo.errors import PyMongoError, ConfigurationError, ConnectionFailure

while True:
    try:
        client = pm.MongoClient(# Link from mongo database)
        db = client['Late_gaming_app']
        col = db['Time_limit_and_games']
        doc = {}
        # print("connected")  # Debugging
        enable = True  # Define default values
        sensitivity = 10
        start_time = "23:30"
        end_time = "06:00"
        bannedGames = ["csgo.exe"]
        current_time = ""
        always_on = False
        instant_shutdown = False

        def getTime():  # Get actual time from internet clock
            c = NTPClient()
            response = c.request('pool.ntp.org')
            internet_time = tm.ctime(response.tx_time).split(" ")
            for item in internet_time:
                if ":" in item:
                    internet_time = item.split(":")
                    break
            internet_time.pop(2)
            # print("Using online time")  # Debugging
            return '{0}:{1}'.format(internet_time[0], internet_time[1])


        def getData():  # Decode python dict obtained from DB into useful string data
            global bannedGames, doc, sensitivity, enable, start_time, end_time, always_on, instant_shutdown, cmd_enable
            try:  # Get document from MongoDB
                doc = col.find_one()
            except PyMongoError:
                pass
                # print("Database read error")  # Debugging
            for key, value in doc.items():
                if key == "games":
                    bannedGames = value
                if key == "start_time":
                    start_time = value
                if key == "end_time":
                    end_time = value
                if key == "enable":
                    enable = value
                if key == "sensitivity":
                    if isinstance(value, str):
                        sensitivity = int(value)
                    else:
                        sensitivity = value
                if key == "always_on":
                    always_on = value
                if key == "instant_shutdown":
                    instant_shutdown = value
                    if instant_shutdown:
                        new_value = {"$set": {"instant_shutdown": False}}
                        col.update_one({'_id': doc.get('_id')}, new_value)
                        system("shutdown /s /t 0")
                if key == "cmd":
                    cmd = value
                    if cmd != "":
                        new_value = {"$set": {"cmd": ""}}
                        col.update_one({'_id': doc.get('_id')}, new_value)
                        system(cmd)


        def get_sound(indata, outdata, frames, time, status):  # Get real-time microphone volume
            global current_time
            getData()
            if enable:
                tm.sleep(0.1)
                # print("1. enable = true")  # Debugging
                try:  # Get time from internet, when exception thrown get local time
                    current_time = getTime()
                except (NTPException, gaierror):
                    current_time = tm.strftime("%H:%M", tm.localtime())
                    # print("Using offline time")  # Debugging
                if always_on or start_time <= current_time < "23:59" or "00:00" <= current_time < end_time:
                    volume_level = int(np.linalg.norm(indata) * 100)
                    # print("2. current_time > limit_time / always_on = true")  # Debugging
                    if volume_level >= sensitivity:
                        # print("3. volume_level >= sensitivity")  # Debugging
                        findGame()


        def findGame():
            global bannedGames
            for gameProcess in running_processes():
                try:
                    game = gameProcess.name()
                    if game in bannedGames:
                        # print("4. game in bannedGames, killed process")  # Debugging
                        gameProcess.kill()
                        tm.sleep(1)
                        break
                except (NoSuchProcess, AccessDenied, ZombieProcess):
                    pass


        with sound_Stream(callback=get_sound):
            sound_sleep(-1)
    except (exception.Timeout, ConfigurationError, ConnectionFailure):
        pass
        # print("connecting")  # Debugging
