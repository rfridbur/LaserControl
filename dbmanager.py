import mysql.connector
import datetime
import time
import sys

# all methods are static - no class is needed

mydb = mysql.connector.connect(
    host="localhost",
    user="ubuntu",
    password="1234567890",
    database="laserdb",
    auth_plugin='mysql_native_password'
)

mycursor = mydb.cursor()
# mydb.autocommit = True

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
                "is_active":machine[4]
            }
        )

    return machines

def add_activity_record(machine_id: int, event_sequence: int, submission_date: datetime, is_active: bool):
    """
    function adds record to [activity] table
    """
    sql = (
        "INSERT INTO activity (machine_id, event_sequence, submission_date, is_active)"
        "VALUES (%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, is_active)
    mycursor.execute(sql, val)

def add_temperature_record(machine_id: int, event_sequence: int, submission_date: datetime, sensor_id: int, value: float):
    """
    function adds record to [temperature] table
    """
    sql = (
        "INSERT INTO temperature (machine_id, event_sequence, submission_date, sensor_id, value)"
        "VALUES (%s,%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, sensor_id, value)
    mycursor.execute(sql, val)

def add_keyswitch_record(machine_id: int, event_sequence: int, submission_date: datetime, is_enabled: bool):
    """
    function adds record to [keyswitch] table
    """
    sql = (
        "INSERT INTO keyswitch (machine_id, event_sequence, submission_date, is_enabled)"
        "VALUES (%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, is_enabled)
    mycursor.execute(sql, val)

def add_error_record(machine_id: int, event_sequence: int, submission_date: datetime, is_error: bool):
    """
    function adds record to [error] table
    """
    sql = (
        "INSERT INTO error (machine_id, event_sequence, submission_date, is_error)"
        "VALUES (%s,%s,%s,%s)"
    )

    val = (machine_id, event_sequence, submission_date, is_error)
    mycursor.execute(sql, val)

def add_machine_record(name: str, ip: str, shared_folder: str, is_active: bool):
    """
    function adds record to [machine] table
    """
    sql = (
        "INSERT INTO machine (name, ip, shared_folder, is_active)"
        "VALUES (%s,%s,%s,%s)"
    )

    val =  (name, ip, shared_folder, is_active)
    mycursor.execute(sql, val)
    commit()

def delete_row_from_table(record_id: int, table: str):
    """
    fucntion delets row id from table
    assumption: column 'id' exists in table
    """
    sql = (
        f'DELETE FROM {table} WHERE id = "{str(record_id)}"'
    )
    mycursor.execute(sql)
    mydb.commit()

def update_machine_record(record_id: int, name: str, ip: str, shared_folder: str, is_active: bool):
    """
    function updates record in [machine] table
    """
    sql = (
        'UPDATE machine '
        f'SET name = "{name}", ip = "{ip}", shared_folder = "{shared_folder}", is_active = {is_active} '
        f'WHERE id = "{str(record_id)}"'
    )

    mycursor.execute(sql)
    commit()

def get_activity_in_last_hours(hours: int) -> list:
    """
    function returns all records from [activity] table in recent hours
    """
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(hours=hours)

    sql = (
        "SELECT * FROM activity "
        f"WHERE submission_date BETWEEN '{start_date}' AND '{end_date}'"
    )

    records = []
    mycursor.execute(sql)
    for record in mycursor.fetchall():
        records.append(
            {
                "machine_id":record[1],
                "submission_date":record[3],
                "is_active":record[4]
            }
        )

    # return all records
    return records

def clear_table_data(table: str):
    """
    function clears all table data
    assumption: table exists
    """
    sql = (
        f'TRUNCATE TABLE {table}'
    )
    mycursor.execute(sql)
    mydb.commit()

def add_operation_record(machine_id: int, submission_date: datetime, is_working: bool):
    """
    function adds record to [operation] table
    """
    sql = (
        "INSERT INTO operation (machine_id, submission_date, is_working)"
        "VALUES (%s,%s,%s)"
    )

    val = (machine_id, submission_date, is_working)
    mycursor.execute(sql, val)

def update_operation_of_last_hours(hours: int):
    """
    function update the [operation] table with [activity] from the last hours
    this is a helper function to ease on queries later that scans the [activity] table
    and extracts the time where laser was active based on assumption that if a laser
    is idle for more than 30 sec, it means that it is not working
    """
    # indicator after which laser becomes inactive
    LASER_INACTIVITY_SEC = 30

    # this is a temporary table, therefore, need to clear it first
    clear_table_data("operation")

    # get all activity in the recent hours
    avtivity_list = get_activity_in_last_hours(hours)

    # determine laser activity and idle time
    # idle time starts when laster is inactive for LASER_INACTIVITY_SEC
    # meaning, look for is_active = 0 and see if it doesn't become active in a given time
    list_len = len(avtivity_list)
    for i in range(list_len):
        # skip first and last items
        if (i == 0) or (i == (list_len - 1)):
            continue

        # get neighbour activities
        prev_item = avtivity_list[i - 1]
        curr_item = avtivity_list[i]
        next_item = avtivity_list[i + 1]

        if curr_item['is_active']:
            # laser is on - check time it was off, compared to previous event
            time_delta = curr_item['submission_date'] - prev_item['submission_date']
        else:
            # laser is off - check time it stays off, compared to next event
            time_delta = next_item['submission_date'] - curr_item['submission_date']

        if time_delta.total_seconds() > LASER_INACTIVITY_SEC:
            # log the current activity
            add_operation_record(curr_item['machine_id'], curr_item['submission_date'], curr_item['is_active'])

    # update [operation] table
    commit()

def commit():
    """
    function commits all recent changes to DB
    """
    mydb.commit()
