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
        # Liste der Skript-Namen, die beendet werden sollen.
        # generate_keywords_bg.py wird hinzugefügt, da es von job_qs.py aufgerufen wird.
        processes_to_kill = [
            "job_qs.py",
            "generate_keywords.py",
            "query_sampler_controller_start.py"
        ]

        print("Searching for processes to terminate...")
        # Iteriert über alle laufenden Prozesse
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Prüft nur Python-Prozesse
                if "python" in proc.info['name'].lower():
                    if proc.info['cmdline']:
                        # Vergleicht die Kommandozeile des Prozesses mit der Kill-Liste
                        cmd_line_str = " ".join(proc.info['cmdline'])
                        for process_name in processes_to_kill:
                            if process_name in cmd_line_str:
                                print(f"Terminating process '{process_name}' with PID {proc.info['pid']}...")
                                proc.kill()
                                print(f"Process {proc.info['pid']} terminated.")
                                # Springe zum nächsten Prozess, da dieser bereits beendet wurde
                                break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Ignoriert Fehler, wenn ein Prozess bereits beendet ist oder keine Zugriffsrechte bestehen
                pass
        
        print("All associated processes have been terminated.")


if __name__ == "__main__":
    # Initialisiert das KeywordController-Objekt
    keyword_controller = KeywordController()

    # Ruft die stop-Methode auf, um die Prozesse zu beenden
    keyword_controller.stop()