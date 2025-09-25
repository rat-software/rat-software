# keyword_controller_stop.py

import psutil
import os
import inspect

class KeywordController:
    """
    Eine Klasse zur Steuerung des Stoppens des Keyword-Generators und der zugehörigen Prozesse.

    Methods:
        stop: Stoppt die relevanten Prozesse.
    """

    def stop(self):
        """
        Sucht und beendet alle Prozesse, die mit der Keyword-Generierung zu tun haben.

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

        print("Suche nach Prozessen zum Beenden...")
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
                                print(f"Beende Prozess '{process_name}' mit PID {proc.info['pid']}...")
                                proc.kill()
                                print(f"Prozess {proc.info['pid']} beendet.")
                                # Springe zum nächsten Prozess, da dieser bereits beendet wurde
                                break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Ignoriert Fehler, wenn ein Prozess bereits beendet ist oder keine Zugriffsrechte bestehen
                pass
        
        print("Alle zugehörigen Prozesse wurden beendet.")


if __name__ == "__main__":
    # Initialisiert das KeywordController-Objekt
    keyword_controller = KeywordController()

    # Ruft die stop-Methode auf, um die Prozesse zu beenden
    keyword_controller.stop()