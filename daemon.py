import time
import datetime
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import dbmanager
import logging
import os
import shutil
import laser
import json
import sys

def mount_logs_folder(shared_folder: str, local_folder: str, user_name: str, domain: str, password: str):
    """
    function maps the shared folder to a local one
    """
    # unmount
    os.system(f"sudo umount -l {local_folder}")

    # delete old folder if exists
    if os.path.exists(local_folder):
        os.system(f"sudo rmdir {local_folder}")

    # create folder
    os.system(f"sudo mkdir {local_folder}")

    # mount
    os.system(f"sudo mount -t cifs -o username={user_name},domain={domain},password={password} {shared_folder} {local_folder}")

def log_daemon_details():
    """
    function logs the daemon details to json file
    >>> PID
    >>> process start time
    """
    data = {
        "pid":os.getpid(),
        "start_time":datetime.datetime.now()
    }

    with open('log.json', 'w') as outfile:
        json.dump(data, outfile, default=json_serializer)

def json_serializer(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

if __name__ == "__main__":

    # create a logger with log file
    now = datetime.datetime.now().strftime("%d_%b_%Y_%H_%M_%S")
    log_file = os.path.join("/media/usbstick/pylogs", now) + ".log"
    # write logs to file and console
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ],
        encoding='utf-8'
    )

    log = logging.getLogger()
    log.info("Laser application has started!")

    # log currebt PID
    log_daemon_details()

    # get all machines from DB
    machines = dbmanager.get_machines()

    # sanity check
    if not machines:
        # no machine were found - exit
        log.error(f"no machines were found in DB")
        sys.exit(1)

    # mount folders to start polling logs
    for machine in machines:
        # use active machines only
        if not machine["is_active"]:
            # machine is disabled - skip
            continue

        shared_folder = os.path.join("//", machine['ip'], machine['shared_folder'])
        local_folder = os.path.join("/", "mnt", "my_drive", machine['name'])

        # handle shared folders
        mount_logs_folder(shared_folder, local_folder, machine['user_name'], machine['domain'], machine['password'])

        # verify "lc.log" exists in the mounted folder
        log_file = os.path.join(local_folder, "lc.log")
        if os.path.exists(log_file):
            # init laser object
            laser.Laser(log, machine, log_file)
        else:
            log.error(f"failed to activate laser {machine['name']} check IP {machine['ip']}")
            log.error(f"file not found in {log_file}")

    SLEEP_TIME_SEC = 1
    LAST_N_HOURS = 120
    sleep_counter = 0
    while True:

        # update operation table once in a minute
        if ((sleep_counter * SLEEP_TIME_SEC) % 60) == 0:
            dbmanager.update_operation_of_last_hours(LAST_N_HOURS)
            log.info(f"operations table was updated with history of {LAST_N_HOURS} last hours")

        # loop forever
        time.sleep(SLEEP_TIME_SEC)
        sleep_counter += 1
