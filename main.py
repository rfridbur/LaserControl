import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import dbmanager
import socket
import json
from fastapi.responses import HTMLResponse
import datetime
import glob
import os

app = FastAPI()

@app.get("/")
async def root():
    host_name = socket.gethostname()
    server_time = datetime.datetime.now()
    last_log_list = get_last_log(10)
    is_running = is_daemon_running()
    daemon_start_time = get_daemon_start_time()
    daemon_pid = get_daemon_pid()
    active_machines = get_active_machines()

    # format msg dict
    root_msg = {
        "message":"go to /docs",
        "home_folder":"/home/ubuntu/laser_server",
        "log_folder":"/media/usbstick/pylogs",
        "server_time":server_time,
        "host_name":host_name,
        "ip_address":socket.gethostbyname(host_name),
        "mysql_port":3306,
        "mysql_db":"laserdb",
        "credentials":[
            {"rpi_user":"ubuntu","password":"1234567890"},
            {"mysql_root_user":"root","password":"Redhat@123456"},
            {"mysql_local_user":"ubuntu","password":"1234567890"},
            {"mysql_remote_user":"remote_user","password":"Redhat@123456"},
        ],
        "daemon":{
            "is_running":is_running,
            "pid":daemon_pid if is_running else 0,
            "start_time":daemon_start_time if is_running else 0,
            "active_machines":active_machines if is_running else None
        },
        "last_logs":last_log_list
    }

    # wrap json with html
    html_content = f'<html><body><pre><code class="prettyprint">{json.dumps(root_msg, default=json_serializer, indent=4)}</code></pre></body></html>'
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/test")
async def test():
    with open('test.html', 'r') as f:
        html_content = f.read()

    return HTMLResponse(content=html_content, status_code=200)

def get_daemon_log_file() -> dict:
    """
    function returns log.json file created by daemon on init
    """
    log_json_file = "/home/ubuntu/laser_server/log.json"
    if os.path.exists(log_json_file):
        with open(log_json_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}

def get_daemon_start_time() -> datetime:
    """
    function returns daemon start time
    """
    data = get_daemon_log_file()
    return data['start_time']

def get_daemon_pid() -> int:
    """
    function returns daemon PID
    """
    data = get_daemon_log_file()
    return data['pid']

def get_active_machines() -> list:
    """
    function returns list of active machines
    """
    return dbmanager.get_active_machines()

def is_daemon_running() -> bool:
    """
    function returns true in case daemon is running
    """
    data = get_daemon_log_file()
    return os.path.isdir(f"/proc/{data['pid']}")

def json_serializer(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def get_last_log(lines: int) -> list:
    """
    function returns last N lines of the latest log file
    assumption: logs are saved int /media/usbstick/pylogs/
    """
    list_of_files = glob.glob('/media/usbstick/pylogs/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        # take the minimal value, in case files is small
        offset = min(lines, len(all_lines))
        return all_lines[-lines:]

class Machine(BaseModel):
    ip: str
    name: str
    shared_folder: str
    is_active: bool
    user_name: str
    domain: str
    password: str

@app.post("/machine")
async def add_item(machine: Machine):
    dbmanager.add_machine_record(machine.name, machine.ip, machine.shared_folder, machine.is_active)
    return machine

@app.get("/machines")
async def get_machines():
    return dbmanager.get_machines()

@app.delete("/machine/{id}")
async def delete_machine(id: int):
    dbmanager.delete_row_from_table(id, "machine")
    return f"machine {id} was deleted successfully"

@app.put("/machine/{id}")
async def update_machine(id: int, machine: Machine):
    dbmanager.update_machine_record(id, machine.name, machine.ip, machine.shared_folder, machine.is_active)
    return f"machine {id} was updated successfully"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)