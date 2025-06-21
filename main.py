# main.py
import sys
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os # Import os for file operations

# Import modules from your project structure
from can_interface import CanInterface
from can_logger import CanLogger
from can_analyzer import CanAnalyzer
from config import CAN_CHANNEL, CAN_BUSTYPE, CAN_BITRATE, LOG_FILE_PATH, LOG_FORMAT

class CanBusApp:
    def __init__(self, master):
        self.master = master
        master.title("CAN Bus Logger & Analyzer")
        master.geometry("800x600") # Set initial window size

        self.can_interface = CanInterface(CAN_CHANNEL, CAN_BUSTYPE, CAN_BITRATE)
        self.can_logger = CanLogger(LOG_FILE_PATH, LOG_FORMAT)
        self.can_analyzer = CanAnalyzer(LOG_FILE_PATH) # Analyzer needs log file path
        
        self.is_logging = False
        self.periodic_sender_active = False
        self.message_counter = 0 # To vary test message data and IDs

        self.create_widgets()

    def create_widgets(self):
        # Connection Frame
        conn_frame = tk.LabelFrame(self.master, text="CAN Connection", padx=10, pady=10)
        conn_frame.pack(pady=10, padx=10, fill='x')

        self.connect_button = tk.Button(conn_frame, text="Connect", command=self.connect_can)
        self.connect_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = tk.Button(conn_frame, text="Disconnect", command=self.disconnect_can, state=tk.DISABLED)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        # Send Test Message and Toggle Periodic Send
        self.send_test_message_button = tk.Button(conn_frame, text="Send Test Msg", command=self.send_test_message, state=tk.DISABLED)
        self.send_test_message_button.pack(side=tk.LEFT, padx=5)

        self.toggle_periodic_send_button = tk.Button(conn_frame, text="Start Periodic Send", command=self.toggle_periodic_send, state=tk.DISABLED)
        self.toggle_periodic_send_button.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(conn_frame, text="Status: Disconnected", fg="red")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Live Messages Display
        msg_frame = tk.LabelFrame(self.master, text="Live CAN Messages", padx=10, pady=10)
        msg_frame.pack(pady=10, padx=10, fill='both', expand=True)

        self.message_display = scrolledtext.ScrolledText(msg_frame, width=80, height=15, state='disabled', wrap='word') # Added wrap for better display
        self.message_display.pack(fill='both', expand=True)

        # Logging Control
        log_frame = tk.LabelFrame(self.master, text="Logging & Analysis", padx=10, pady=10)
        log_frame.pack(pady=10, padx=10, fill='x')

        self.log_button = tk.Button(log_frame, text="Start Logging", command=self.toggle_logging, state=tk.DISABLED)
        self.log_button.pack(side=tk.LEFT, padx=5)

        self.analyze_button = tk.Button(log_frame, text="Analyze Log", command=self.run_analysis)
        self.analyze_button.pack(side=tk.LEFT, padx=5)

        self.clear_display_button = tk.Button(log_frame, text="Clear Display", command=self.clear_display)
        self.clear_display_button.pack(side=tk.RIGHT, padx=5)


    def update_status(self, message, color="black"):
        self.status_label.config(text=f"Status: {message}", fg=color)

    def connect_can(self):
        if self.can_interface.connect():
            self.update_status("Connected", "green")
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.log_button.config(state=tk.NORMAL)
            self.send_test_message_button.config(state=tk.NORMAL) # Enable send button
            self.toggle_periodic_send_button.config(state=tk.NORMAL) # Enable periodic send button
            
            # Start listening for messages after successful connection
            self.can_interface.start_listening(callback=self.display_message)
        else:
            self.update_status("Connection Failed", "red")
            messagebox.showerror("Connection Error", "Failed to connect to CAN bus. Check configuration and hardware.")

    def disconnect_can(self):
        # Stop periodic sender if active
        if self.periodic_sender_active:
            self.toggle_periodic_send() 
        # Stop logging if active
        if self.is_logging:
            self.toggle_logging() 
        
        self.can_interface.disconnect()
        self.update_status("Disconnected", "red")
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.log_button.config(state=tk.DISABLED)
        self.send_test_message_button.config(state=tk.DISABLED) # Disable send button
        self.toggle_periodic_send_button.config(state=tk.DISABLED) # Disable periodic send button

    def display_message(self, msg):
        # Tkinter UI updates must be done on the main thread.
        # If this callback is from a different thread (like Notifier's thread),
        # use master.after to schedule it.
        # The current implementation of can.Notifier often calls callbacks on its own thread.
        self.master.after(0, lambda: self._update_message_display(msg))

    def _update_message_display(self, msg):
        formatted_msg = (
            f"[{msg.timestamp:.4f}] ID: 0x{msg.arbitration_id:03X} "
            f"DLC: {msg.dlc} Data: {msg.data.hex().upper()} "
            f"{'(Extended)' if msg.is_extended_id else ''} "
            f"{'(Remote)' if msg.is_remote_frame else ''} "
            f"{'(Error)' if msg.is_error_frame else ''}\n"
        )
        self.message_display.config(state='normal')
        self.message_display.insert(tk.END, formatted_msg)
        self.message_display.see(tk.END) # Auto-scroll to bottom
        self.message_display.config(state='disabled')

        if self.is_logging:
            self.can_logger.log_message(msg)

    def toggle_logging(self):
        if not self.is_logging:
            # When starting logging, remove previous log file to ensure fresh start
            if os.path.exists(self.can_logger.log_file_path):
                try:
                    os.remove(self.can_logger.log_file_path)
                    print(f"Removed existing log file: {self.can_logger.log_file_path}")
                except OSError as e:
                    print(f"Error removing old log file {self.can_logger.log_file_path}: {e}. Please close any programs using it.")
                    messagebox.showerror("File Error", f"Could not remove old log file: {e}\nPlease ensure it's not open in another program.")
                    return # Don't start logging if old file can't be removed

            self.can_logger._open_file() # Ensure file is open for logging
            if self.can_logger.file_opened:
                self.is_logging = True
                self.log_button.config(text="Stop Logging", bg="red")
                self.update_status("Logging Active", "blue")
            else:
                messagebox.showerror("Logging Error", "Could not open log file.")
        else:
            self.is_logging = False
            self.can_logger.close()
            self.log_button.config(text="Start Logging", bg="SystemButtonFace") # Default button color
            self.update_status("Logging Stopped", "black")

    def send_test_message(self):
        if self.can_interface.is_connected:
            try:
                self.message_counter += 1
                # Vary data for better analysis
                data_bytes = [(self.message_counter % 256), (self.message_counter + 1) % 256, (self.message_counter + 2) % 256, 0x03, 0x04, 0x05, 0x06, 0x07]
                
                # Send different IDs to get some variety for analysis plot
                if self.message_counter % 3 == 0:
                    can_id = 0x100 # Common ID
                elif self.message_counter % 3 == 1:
                    can_id = 0x200 # Another common ID
                else:
                    can_id = 0x300 # A third common ID
                
                self.can_interface.send_message(can_id, data_bytes)
                # print(f"Sent single message: 0x{can_id:X}") # For console debugging if needed
            except Exception as e:
                messagebox.showerror("Send Error", f"Failed to send message: {e}")
        else:
            messagebox.showwarning("Send Warning", "Not connected to CAN bus.")

    def periodic_sender(self):
        while self.periodic_sender_active and self.can_interface.is_connected:
            self.send_test_message()
            time.sleep(0.1) # Send every 100ms (adjust as needed)

    def toggle_periodic_send(self):
        if not self.periodic_sender_active:
            if self.can_interface.is_connected:
                self.periodic_sender_active = True
                # Start the periodic sender in a separate daemon thread
                self.periodic_send_thread = threading.Thread(target=self.periodic_sender, daemon=True)
                self.periodic_send_thread.start()
                self.toggle_periodic_send_button.config(text="Stop Periodic Send", bg="orange")
                self.update_status("Periodic Sending Active", "purple")
            else:
                messagebox.showwarning("Send Warning", "Connect to CAN bus first to start periodic sending.")
        else:
            self.periodic_sender_active = False
            # The thread will exit its loop naturally due to the flag becoming False
            # No need to explicitly join unless you need to wait for it.
            self.toggle_periodic_send_button.config(text="Start Periodic Send", bg="SystemButtonFace")
            self.update_status("Periodic Sending Stopped", "black")

    def run_analysis(self):
        # Always stop logging first to ensure all data is written to file
        if self.is_logging:
            self.toggle_logging() 

        if not self.can_analyzer.load_log_data():
            messagebox.showerror("Analysis Error", "Failed to load log data. Ensure logging was active and data was captured.")
            return

        # Check if DataFrame is empty after loading
        if self.can_analyzer.df.empty:
            messagebox.showinfo("Analysis Info", "No messages found in the log file for analysis.")
            return

        summary = self.can_analyzer.get_message_summary()
        if summary:
            summary_text = "\n--- Log Summary ---\n"
            for key, value in summary.items():
                summary_text += f"{key}: {value}\n"
            messagebox.showinfo("Analysis Summary", summary_text)
            
            # Offer to plot only if there's data to plot
            if messagebox.askyesno("Analysis", "Do you want to see message frequency plot?"):
                self.can_analyzer.plot_message_frequency()

    def clear_display(self):
        self.message_display.config(state='normal')
        self.message_display.delete(1.0, tk.END)
        self.message_display.config(state='disabled')


    def on_closing(self):
        # Ensure all threads and connections are properly shut down
        if self.periodic_sender_active:
            self.toggle_periodic_send()
        if self.is_logging:
            self.toggle_logging() # Ensure log file is closed
        self.can_interface.disconnect()
        self.master.destroy() # Destroy the Tkinter window

if __name__ == "__main__":
    # Create the Tkinter root window
    root = tk.Tk()
    # Create an instance of your application
    app = CanBusApp(root)
    # Set up the protocol for window closing (e.g., clicking 'X')
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    # Start the Tkinter event loop
    root.mainloop()