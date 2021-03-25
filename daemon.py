import time
import datetime
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import dbmanager
import logging
import os
import shutil
import laser

def mount_logs_folder(shared_folder:str, local_folder:str):
    """
    function maps the shared folder to a local one
    """
    # credentials
    user_name = "rfridbur"
    domain = "ger"
    password = "fhpvxdukv@7102"

    # unmount
    os.system(f"sudo umount -l {local_folder}")

    # delete old folder if exists
    if os.path.exists(local_folder):
        os.system(f"sudo rmdir {local_folder}")

    # create folder
    os.system(f"sudo mkdir {local_folder}")

    # mount
    os.system(f"sudo mount -t cifs -o username={user_name},domain={domain},password={password} {shared_folder} {local_folder}")

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

    # get all machines from DB
    machines = dbmanager.get_machines()

    # sanity check
    if not machines:
        # no machine were found - exit
        log.error(f"no machines were found in DB")
        sys.exit(1)

    # mount folders to start polling logs
    for machine in machines:
        shared_folder = os.path.join("//", machine['ip'], machine['shared_folder'])
        local_folder = os.path.join("/", "mnt", "my_drive", machine['name'])

        # handle shared folders
        mount_logs_folder(shared_folder, local_folder)

        # verify "lc.txt" exists in the mounted folder
        log_file = os.path.join(local_folder, "lc.txt")
        if not os.path.exists(log_file):
            log.error(f"file not found in {log_file}")
            sys.exit(1)

        # init laser object
        laser.Laser(log, machine, log_file)

    while True:
        time.sleep(1)