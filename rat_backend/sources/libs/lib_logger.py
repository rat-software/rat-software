from datetime import datetime

class Logger:
    """
    A simple logger class that writes log messages to a file with a timestamp.
    """

    def __init__(self):
        """
        Initializes the Logger instance.
        """
        # Initialization logic can be added here if needed
        pass

    def __del__(self):
        """
        Destructor for the Logger class, which is called when the object is destroyed.
        """
        print('Logger object destroyed')

    def write_to_log(self, log):
        """
        Writes a log message to the log file with a timestamp.

        Args:
            log (str): The log message to be written to the log file.
        """
        # Get the current timestamp
        timestamp = datetime.now()
        # Format the timestamp as a string
        timestamp_str = timestamp.strftime("%d-%m-%Y, %H:%M:%S")
        
        # Open the log file in append mode
        with open("sources_scraper.log", "a") as f:
            # Write the timestamp and log message to the file
            f.write(f"{timestamp_str}: {log}\n")
