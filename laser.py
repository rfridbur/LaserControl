from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import difflib
import re
import dbmanager
import time
import datetime
import threading

# const
TIME_FORMAT = '\d+-\d+-\d+ \d+:\d+:\d+,\d+'

class Laser():
    def __init__(self, log, machine, log_file):
        self.__log = log
        self.__id = machine['id']
        self.__name = machine['name']
        self.__ip = machine['ip']
        self.__log_file = log_file
        self.__orig_file_content = ""
        self.__diff = difflib.Differ()
        self.__lock = threading.Lock()
        self.__event_id = 0
        self.__db_update_lines = 0

        # start observer
        self.__event_handler = FileSystemEventHandler()
        self.__event_handler.on_modified = self.__on_modified
        self.__observer = PollingObserver()
        self.__observer.schedule(self.__event_handler, path=self.__log_file)
        self.__observer.start()

        self.__log.info(f"laster initialized for {self.__name} [{self.__ip}]")

    def __on_modified(self, event):
        """
        even handler for modified file
        function is called when file is being modified
        handling is done under lock, in order to avoid multiple parallel instances
        """
        total_lines_count = 0
        self.__db_update_lines = 0
        start_time = datetime.datetime.now()
        # critical section - start
        self.__lock.acquire()

        self.__log.info(f'event type: {event.event_type}  path: {event.src_path}')
        new_file = self.__get_file_content(self.__log_file)

        # the log file is incremental, therefore, to ignore previous changes
        # which were already handled and parsed -> use the difflib
        # need to keep the original copy and make 'diff' versus the new one
        # the difflib presents that data in git-diff style, where
        # added lines are represented with '+', while removed are with '-'
        # basically, for our purposes, we are interested only in new lines
        # therefore, all the regex are started with '+'
        for line in self.__diff.compare(self.__orig_file_content.splitlines(), new_file.splitlines()):
            if line.startswith("+"):
                total_lines_count += 1
                if self.__match_activity(line): continue
                if self.__match_temperature(line): continue
                if self.__match_keyswitch(line): continue
                if self.__match_error(line): continue

        # commit all the changes
        dbmanager.commit()
        self.__orig_file_content = new_file

        # critical section - end
        self.__lock.release()
        end_time = datetime.datetime.now()
        delta = end_time - start_time
        self.__log.debug(f"total lines: {total_lines_count} db update: {self.__db_update_lines}, parse time: {delta.seconds} [s] {delta.microseconds} [us]")

    def __get_file_content(self, file:str) -> str:
        """
        function returns file content
        """
        with open(file, 'r') as f:
            return f.read()

    def __str_to_bool(self, mystr:str) -> bool:
        """
        function converts boolean str to bool
        e.g. "True" -> True
        """
        return (mystr.lower().strip() == "true")

    def __str_to_datetime(self, datestr:str) -> time:
        """
        function converts date time str from laser log to datetime type
        """
        return time.strptime(datestr, '%Y-%m-%d %H:%M:%S,%f')

    def __str_to_float(self, floatstr:str) -> float:
        """
        function converts float str from laser log to float type
        leave 4 significant digits (e.g 27.34)
        """
        return format(float(floatstr.replace(",",".")), '.4g')

    def __get_incremented_event_id(self) -> int:
        """
        function generates event id by incrementing the orig one
        assumption: function runs under lock
        """
        self.__event_id = self.__event_id + 1
        return self.__event_id

    def __match_activity(self, line:str) -> bool:
        """
        function is responsible to match the laser activity
        returns true/false in case match was found
        """
        match = re.findall(f'\+ ({TIME_FORMAT}).*busy Value: (\S+)', line)
        if match:
            event_sequence = self.__get_incremented_event_id()
            submission_date = self.__str_to_datetime(match[0][0])
            is_active = self.__str_to_bool(match[0][1])
            dbmanager.add_activity_record(self.__id, event_sequence, submission_date, is_active)
            self.__db_update_lines += 1

    def __match_temperature(self, line:str) -> bool:
        """
        function is responsible to match the laser temperature
        returns true/false in case match was found
        """
        match = re.findall(f'\+ ({TIME_FORMAT}).*temperature(\d) Value: (\S+)', line)
        if match:
            event_sequence = self.__get_incremented_event_id()
            submission_date = self.__str_to_datetime(match[0][0])
            sensor_id = int(match[0][1])
            value = self.__str_to_float(match[0][2])
            dbmanager.add_temperature_record(self.__id, event_sequence, submission_date, sensor_id, value)
            self.__db_update_lines += 1

    def __match_keyswitch(self, line:str) -> bool:
        """
        function is responsible to match the laser keyswitch (door open/close)
        returns true/false in case match was found
        """
        match = re.findall(f'\+ ({TIME_FORMAT}).*keySwitchPos Value: (\S+)', line)
        if match:
            event_sequence = self.__get_incremented_event_id()
            submission_date = self.__str_to_datetime(match[0][0])
            is_enabled = self.__str_to_bool(match[0][1])
            dbmanager.add_keyswitch_record(self.__id, event_sequence, submission_date, is_enabled)
            self.__db_update_lines += 1

    def __match_error(self, line:str) -> bool:
        """
        function is responsible to match the laser error
        returns true/false in case match was found
        """
        match = re.findall(f'\+ ({TIME_FORMAT}).*error Value: (\S+)', line)
        if match:
            event_sequence = self.__get_incremented_event_id()
            submission_date = self.__str_to_datetime(match[0][0])
            is_error = self.__str_to_bool(match[0][1])
            dbmanager.add_error_record(self.__id, event_sequence, submission_date, is_error)
            self.__db_update_lines += 1