# can_analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import os

class CanAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.df = None

    def load_log_data(self):
        if not os.path.exists(self.log_file_path):
            print(f"Error: Log file not found at {self.log_file_path}")
            return False
        
        # Check if the file is empty (only header or completely empty)
        if os.path.getsize(self.log_file_path) == 0:
            print(f"Log file {self.log_file_path} is empty.")
            self.df = pd.DataFrame(columns=['timestamp', 'arbitration_id', 'is_extended_id', 'is_remote_frame', 'is_error_frame', 'dlc', 'data'])
            return True # Return True, but with an empty DataFrame

        try:
            self.df = pd.read_csv(self.log_file_path)
            print(f"Loaded {len(self.df)} messages from {self.log_file_path}")
            return True
        except pd.errors.EmptyDataError:
            print(f"Log file {self.log_file_path} contains no data rows (only header or empty).")
            self.df = pd.DataFrame(columns=['timestamp', 'arbitration_id', 'is_extended_id', 'is_remote_frame', 'is_error_frame', 'dlc', 'data'])
            return True # Successfully loaded an empty dataframe
        except Exception as e:
            print(f"Error loading log data: {e}")
            return False

    def get_message_summary(self):
        if self.df is None or self.df.empty:
            print("No data loaded or DataFrame is empty.")
            return None
        
        # Convert arbitration_id to numeric for proper unique counting if stored as '0x123'
        # Or ensure it's loaded as string if you prefer.
        # Assuming '0xABC' string format for common ID summary
        
        summary = {
            "total_messages": len(self.df),
            "unique_can_ids": self.df['arbitration_id'].nunique(),
            "most_common_ids": self.df['arbitration_id'].value_counts().head(5).to_dict(),
            "start_time": self.df['timestamp'].min(),
            "end_time": self.df['timestamp'].max(),
            "duration_seconds": self.df['timestamp'].max() - self.df['timestamp'].min()
        }
        return summary

    def filter_by_can_id(self, can_id):
        if self.df is None or self.df.empty:
            print("No data loaded. Call load_log_data() first.")
            return pd.DataFrame() # Return empty DataFrame

        # Ensure comparison is consistent (e.g., convert loaded ID to int if needed)
        # Assuming 'arbitration_id' in CSV is stored as '0x123' string
        can_id_hex_str = f"0x{can_id:X}"
        filtered_df = self.df[self.df['arbitration_id'] == can_id_hex_str]
        print(f"Filtered {len(filtered_df)} messages for CAN ID: {can_id_hex_str}")
        return filtered_df

    def plot_message_frequency(self, top_n=10):
        if self.df is None or self.df.empty:
            print("No data loaded or DataFrame is empty. Cannot plot.")
            # Use messagebox to inform the user in the GUI context
            plt.figure().set_visible(False) # Create a blank figure and make it invisible
            plt.close() # Close it immediately
            return

        id_counts = self.df['arbitration_id'].value_counts().head(top_n)
        
        if id_counts.empty:
            print("No message IDs to plot (id_counts is empty).")
            plt.figure().set_visible(False)
            plt.close()
            return

        plt.figure(figsize=(10, 6))
        id_counts.plot(kind='bar')
        plt.title(f'Top {len(id_counts)} Most Frequent CAN IDs')
        plt.xlabel('CAN ID')
        plt.ylabel('Frequency')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    # Add more analysis functions as needed:
    # - analyze_data_patterns(can_id, byte_index)
    # - calculate_average_dlc()
    # - detect_missing_messages(expected_ids)

# Example Usage (for testing can_analyzer.py independently)
if __name__ == "__main__":
    from config import LOG_FILE_PATH, TARGET_CAN_ID_FOR_ANALYSIS
    import can # For creating dummy messages if no log exists
    import time

    # Ensure a log file exists for testing
    if not os.path.exists(LOG_FILE_PATH) or os.path.getsize(LOG_FILE_PATH) == 0:
        print(f"'{LOG_FILE_PATH}' not found or is empty. Creating a dummy one for analysis test.")
        with open(LOG_FILE_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'arbitration_id', 'is_extended_id', 'is_remote_frame', 'is_error_frame', 'dlc', 'data'])
            # Add some dummy data
            writer.writerow([time.time(), '0x100', False, False, False, 8, '0102030405060708'])
            writer.writerow([time.time()+0.1, '0x200', False, False, False, 4, 'aabbccdd'])
            writer.writerow([time.time()+0.2, '0x100', False, False, False, 8, '090a0b0c0d0e0f10'])
            writer.writerow([time.time()+0.3, '0x300', False, False, False, 8, '1122334455667788'])
            writer.writerow([time.time()+0.4, '0x100', False, False, False, 8, 'fedcba9876543210'])
        print(f"Created a dummy '{LOG_FILE_PATH}' for testing analysis.")


    analyzer = CanAnalyzer(LOG_FILE_PATH)

    if analyzer.load_log_data():
        summary = analyzer.get_message_summary()
        if summary:
            print("\n--- Log Summary ---")
            for key, value in summary.items():
                print(f"{key}: {value}")

        print("\n--- Filtering messages for 0x100 ---") # Updated to 0x100 for dummy data
        filtered_messages = analyzer.filter_by_can_id(0x100)
        print(filtered_messages.head())

        print("\n--- Plotting Message Frequency ---")
        analyzer.plot_message_frequency()