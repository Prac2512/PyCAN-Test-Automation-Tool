# can_interface.py
import can
import time
import threading

class CanInterface:
    def __init__(self, channel, bustype, bitrate):
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.bus = None
        self.is_connected = False
        # self.received_messages = [] # Not used directly in this version with callback
        # self._lock = threading.Lock() # Not used directly in this version with callback
        self.listener_thread = None

    def connect(self):
        try:
            # For virtual bus, `can.Bus` directly creates the virtual interface
            self.bus = can.interface.Bus(channel=self.channel, bustype=self.bustype, bitrate=self.bitrate)
            self.is_connected = True
            print(f"Successfully connected to CAN bus: {self.bustype} on {self.channel} at {self.bitrate} bps")
            return True
        except Exception as e:
            print(f"Error connecting to CAN bus ({self.bustype}, {self.channel}): {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        if self.bus:
            # If a listener thread is active, it will naturally stop when is_connected becomes False
            self.bus.shutdown()
            self.is_connected = False
            print("Disconnected from CAN bus.")

    def start_listening(self, callback=None):
        if not self.is_connected:
            print("Not connected to CAN bus. Cannot start listening.")
            return

        def receive_loop():
            # Use a Notifier for asynchronous reception, which is more robust for GUIs
            # Note: The Notifier processes messages on its own internal thread.
            # The callback will be called from that thread, so ensure UI updates are thread-safe (handled by Tkinter's mainloop)
            self.notifier = can.Notifier(self.bus, [callback], timeout=1.0) # Pass the callback directly
            # The loop here is just to keep the thread alive while notifier runs
            while self.is_connected:
                time.sleep(0.1) # Small sleep to not busy-wait

        if self.listener_thread is None or not self.listener_thread.is_alive():
            self.listener_thread = threading.Thread(target=receive_loop, daemon=True)
            self.listener_thread.start()
            print("Started listening for CAN messages.")
        else:
            print("Listener thread is already running.")


    def send_message(self, arbitration_id, data, is_extended_id=False):
        if not self.is_connected:
            # print("Not connected to CAN bus. Cannot send message.") # Suppress for periodic sender
            return False
        try:
            msg = can.Message(arbitration_id=arbitration_id,
                              data=data,
                              is_extended_id=is_extended_id)
            self.bus.send(msg)
            # print(f"Sent: {msg}") # Suppress for periodic sender to avoid console spam
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

# Example Usage (for testing can_interface.py independently)
if __name__ == "__main__":
    from config import CAN_CHANNEL, CAN_BUSTYPE, CAN_BITRATE

    can_interface = CanInterface(CAN_CHANNEL, CAN_BUSTYPE, CAN_BITRATE)

    # For testing virtual bus, we need another bus to send to it
    # OR you can enable bus.recv(receive_own_messages=True) if your hardware supports it.
    # For virtual, it automatically receives its own messages.

    if can_interface.connect():
        def print_and_log_message(msg):
            # This would be a simplified version of what display_message does in main.py
            print(f"Received: {msg.timestamp:.4f} ID: 0x{msg.arbitration_id:X} Data: {msg.data.hex()}")

        can_interface.start_listening(callback=print_and_log_message)

        print("\nSending some dummy messages...")
        for i in range(5):
            can_interface.send_message(0x100 + i, [i, i*2, i*3])
            time.sleep(0.1)

        print("\nLetting it run for a few seconds to receive...")
        time.sleep(3) # Let the listener receive messages

        can_interface.disconnect()
        print("Test finished.")