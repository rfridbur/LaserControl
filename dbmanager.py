import mysql.connector
import datetime
import time

# all methods are static - no class is needed

mydb = mysql.connector.connect(
    host="localhost",
    user="ubuntu",
    password="1234567890",
    database="laserdb",
    auth_plugin='mysql_native_password'
)

mycursor = mydb.cursor()

def get_machines() -> list:
    """
    function returns all machines from [machine] table
    """
    sql = (
        "SELECT * FROM machine"
    )

    machines = []
    mycursor.execute(sql)
    for machine in mycursor.fetchall():
        machines.append(
            {
                "id":machine[0],
                "name":machine[1],
                "ip":machine[2],
                "shared_folder":machine[3],
            }
        )
    
    return machines

def add_activity_record(machine_id:int, event_sequence:int, submission_date:datetime, is_active:bool):
    """
    function adds record to [activity] table
    """
    sql = (
        "INSERT INTO activity (machine_id, event_sequence, submission_date, is_active)"
        "VALUES (%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, is_active)
    mycursor.execute(sql, val)

def add_temperature_record(machine_id:int, event_sequence:int, submission_date:datetime, sensor_id:int, value:float):
    """
    function adds record to [temperature] table
    """
    sql = (
        "INSERT INTO temperature (machine_id, event_sequence, submission_date, sensor_id, value)"
        "VALUES (%s,%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, sensor_id, value)
    mycursor.execute(sql, val)

def add_keyswitch_record(machine_id:int, event_sequence:int, submission_date:datetime, is_enabled:bool):
    """
    function adds record to [keyswitch] table
    """
    sql = (
        "INSERT INTO keyswitch (machine_id, event_sequence, submission_date, is_enabled)"
        "VALUES (%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, is_enabled)
    mycursor.execute(sql, val)

def add_error_record(machine_id:int, event_sequence:int, submission_date:datetime, is_error:bool):
    """
    function adds record to [error] table
    """
    sql = (
        "INSERT INTO error (machine_id, event_sequence, submission_date, is_error)"
        "VALUES (%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, is_error)
    mycursor.execute(sql, val)

def commit():
    """
    function commits all recent changes to DB
    """
    mydb.commit()