# can_logger.py
import csv
import os
from datetime import datetime

class CanLogger:
    def __init__(self, log_file_path, log_format):
        self.log_file_path = log_file_path
        self.log_format = log_format
        self.file = None
        self.writer = None
        self.file_opened = False

    def _open_file(self):
        try:
            # Append to file, create if not exists. Write header if new file or empty file.
            file_exists = os.path.exists(self.log_file_path)
            self.file = open(self.log_file_path, 'a', newline='')
            self.writer = csv.writer(self.file)
            # Check if file is empty or newly created to write header
            if not file_exists or os.path.getsize(self.log_file_path) == 0:
                self.writer.writerow(self.log_format) # Write header
            self.file_opened = True
            print(f"Logging to: {self.log_file_path}")
        except IOError as e:
            print(f"Error opening log file {self.log_file_path}: {e}")
            self.file_opened = False

    def log_message(self, msg):
        if not self.file_opened:
            # This should ideally be called once before logging starts (e.g., by toggle_logging)
            # But as a fallback, try to open if not already.
            self._open_file()
            if not self.file_opened:
                return # Can't log if file couldn't be opened

        try:
            row = []
            for field in self.log_format:
                if field == 'timestamp':
                    row.append(msg.timestamp)
                elif field == 'arbitration_id':
                    row.append(f"0x{msg.arbitration_id:X}") # Hex format
                elif field == 'is_extended_id':
                    row.append(msg.is_extended_id)
                elif field == 'is_remote_frame':
                    row.append(msg.is_remote_frame)
                elif field == 'is_error_frame':
                    row.append(msg.is_error_frame)
                elif field == 'dlc':
                    row.append(msg.dlc)
                elif field == 'data':
                    row.append(msg.data.hex()) # Hex string for data
                else:
                    row.append('') # Placeholder for unknown/unmatched fields

            self.writer.writerow(row)
            self.file.flush() # Ensure data is written to disk immediately
        except Exception as e:
            print(f"Error logging message: {e}")

    def close(self):
        if self.file_opened and self.file:
            self.file.close()
            self.file = None # Clear file handle
            self.writer = None # Clear writer
            self.file_opened = False
            print("Log file closed.")

# Example Usage (for testing can_logger.py independently)
if __name__ == "__main__":
    from config import LOG_FILE_PATH, LOG_FORMAT
    import can # For creating dummy messages
    import time
    import os

    # Clean up previous log for clear test
    if os.path.exists(LOG_FILE_PATH):
        os.remove(LOG_FILE_PATH)
        print(f"Removed existing log file: {LOG_FILE_PATH}")

    logger = CanLogger(LOG_FILE_PATH, LOG_FORMAT)

    # Simulate receiving messages
    dummy_messages = [
        can.Message(timestamp=time.time(), arbitration_id=0x123, is_extended_id=False, dlc=8, data=[1, 2, 3, 4, 5, 6, 7, 8]),
        can.Message(timestamp=time.time() + 0.1, arbitration_id=0x456, is_extended_id=False, dlc=4, data=[0xA, 0xB, 0xC, 0xD]),
        can.Message(timestamp=time.time() + 0.2, arbitration_id=0x123, is_extended_id=False, dlc=8, data=[9, 8, 7, 6, 5, 4, 3, 2])
    ]

    for msg in dummy_messages:
        logger.log_message(msg)
        time.sleep(0.05) # Simulate some delay

    logger.close()
    print(f"Check '{LOG_FILE_PATH}' for logged data.")