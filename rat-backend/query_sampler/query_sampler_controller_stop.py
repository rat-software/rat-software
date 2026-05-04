# keyword_controller_stop.py

import psutil
import os
import inspect

class KeywordController:
    """
    A class for controlling the shutdown of the keyword generator and its associated processes.

    Methods:
        stop: Stops the relevant processes.
    """

    def stop(self):
        """
        Find and terminate all processes related to keyword generation.

        Returns:
            None
        """
        # List of script names to be terminated.
        # generate_keywords_bg.py is added because it is called by job_qs.py.
        processes_to_kill = [
            "job_qs.py",
            "generate_keywords.py",
            "query_sampler_controller_start.py",
            "job_reset_qs.py",
            "qs_reset.py"
        ]

        print("Searching for processes to terminate...")
        # Iterates over all running processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                
                if "python" in proc.info['name'].lower():
                    if proc.info['cmdline']:
                        # Compares the process's command line with the kill list
                        cmd_line_str = " ".join(proc.info['cmdline'])
                        for process_name in processes_to_kill:
                            if process_name in cmd_line_str:
                                print(f"Terminating process '{process_name}' with PID {proc.info['pid']}...")
                                proc.kill()
                                print(f"Process {proc.info['pid']} terminated.")
                                break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Ignores errors if a process has already terminated or if there are no access permissions
                pass
        
        print("All associated processes have been terminated.")


if __name__ == "__main__":
    # Initializes the KeywordController object
    keyword_controller = KeywordController()

    # Calls the stop method to terminate the processes
    keyword_controller.stop()