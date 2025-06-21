# config.py

# CAN Interface Configuration
# For virtual bus, set bustype to 'virtual' and channel to any string name (e.g., 'my_virtual_can')
# For real hardware, example for Peak-CAN: CAN_CHANNEL = 'PCAN_USBBUS1', CAN_BUSTYPE = 'pcan'
# For SocketCAN on Linux: CAN_CHANNEL = 'can0', CAN_BUSTYPE = 'socketcan'
CAN_CHANNEL = 'my_virtual_can'  # Use a string name for virtual bus
CAN_BUSTYPE = 'virtual'         # 'pcan', 'vector', 'socketcan', 'virtual', etc.
CAN_BITRATE = 500000            # 500 kbps (bitrate is less relevant for virtual, but good practice)

# Logging Configuration
LOG_FILE_PATH = 'can_log.csv'
# Format of the data logged to CSV. Ensure consistency with how you extract data from can.Message
LOG_FORMAT = [
    'timestamp',
    'arbitration_id',
    'is_extended_id',
    'is_remote_frame',
    'is_error_frame',
    'dlc',
    'data' # Hex string representation of data bytes
]

# Analysis Configuration (example - not directly used in the current main.py, but useful for analyzer.py's own tests)
TARGET_CAN_ID_FOR_ANALYSIS = 0x123 # Example CAN ID to focus analysis on