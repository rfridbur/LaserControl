import mysql.connector
import datetime
import time
import sys
import threading

# all methods are static - no class is needed

mydb = mysql.connector.connect(
    host="localhost",
    user="ubuntu",
    password="1234567890",
    database="laserdb",
    auth_plugin='mysql_native_password'
)

# global variable, common to all instances
# needed to synchronize all SQL inserts
lock = threading.Lock()

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
                "is_active":machine[4],
                "user_name":machine[5],
                "domain":machine[6],
                "password":machine[7]
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

def get_activity_in_last_hours(hours: int, machine_id: int) -> list:
    """
    function returns all records from [activity] table in recent hours
    """
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(hours=hours)

    sql = (
        "SELECT * FROM activity "
        f"WHERE submission_date BETWEEN '{start_date}' AND '{end_date}' AND machine_id = {machine_id}"
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

def add_operation_record(machine_id: int, submission_date: datetime, is_working: bool, duration_sec: int):
    """
    function adds record to [operation] table
    """
    sql = (
        "INSERT INTO operation (machine_id, submission_date, is_working, duration_sec)"
        "VALUES (%s,%s,%s,%s)"
    )

    val = (machine_id, submission_date, is_working, duration_sec)
    mycursor.execute(sql, val)

def update_operation_of_last_hours(hours: int):
    """
    function updates the [operation] table with [activity] from the last hours
    this is a helper function to ease on queries later that scan the [activity] table
    and extracts the time where laser was active based on assumption that if a laser
    is idle for more than 30 sec, it means that it is not working
    """
    # critical section - start
    lock.acquire()

    # indicator after which laser becomes inactive
    LASER_INACTIVITY_SEC = 30

    # this is a temporary table, therefore, need to clear it first
    clear_table_data("operation")

    # need to generate sublists per machine
    active_machine_list = get_active_machines()
    for active_machine in active_machine_list:
        machine_id = get_machine_id_from_name(active_machine)

        # get all activity in the recent hours
        avtivity_list = get_activity_in_last_hours(hours, machine_id)

        # determine laser activity and idle time
        # idle time starts when laster is inactive for LASER_INACTIVITY_SEC
        # meaning, look for is_active = 0 and see if it doesn't become active in a given time
        list_len = len(avtivity_list)
        i = 1
        # skip first and last items
        while i < (list_len - 1):

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
                # add the duration (of idle or busy to the table to ease on querries later - utilziation)
                add_operation_record(curr_item['machine_id'], curr_item['submission_date'], curr_item['is_active'], time_delta.total_seconds())
                # debug log
                # is_active_str = "active" if curr_item['is_active'] else "not avtive"
                # print(f"{active_machine} was {is_active_str} for {time_delta.total_seconds()} [sec]")

            # go to next activity
            i += 1

    # update [operation] table
    commit()

    # critical section - end
    lock.release()

def get_machine_id_from_name(machine_name: str) -> int:
    """
    function returns machine ID by name (looks for active machines only)
    >>> example: FR4 --> 8
    """
    sql = (
        "SELECT id FROM machine "
        f"WHERE name = '{machine_name}' AND is_active = True"
    )
    
    mycursor.execute(sql)
    return mycursor.fetchall()[0][0]

def get_active_machines() -> list:
    """
    function returns the active machines that having records in [temperature]
    table for the 100 records. lasers time can be shifted, therefore, use top IDs
    """
    sql = (
        "SELECT machine.name, temperature.id "
        "FROM machine INNER JOIN temperature ON machine.id = temperature.machine_id "
        "ORDER BY temperature.id DESC "
        "LIMIT 100"
    )

    records = set()
    mycursor.execute(sql)
    for record in mycursor.fetchall():
        records.add(record[0])

    # return all records
    return list(records)

def commit():
    """
    function commits all recent changes to DB
    """
    mydb.commit()
