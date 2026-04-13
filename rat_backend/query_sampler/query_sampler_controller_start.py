# keyword_controller_start.py

import threading
import os
import inspect

class KeywordController:
    """
    A class for controlling the startup of the keyword generator.

    Methods:
        start: Starts the job scheduler for keyword generation.
    """

    def start(self, workingdir: str):
        """
        Starts the scheduler for keyword generation.

        Args:
            workingdir (str): The working directory where the 'jobs' directory is located.

        Returns:
            None
        """
        def start_job():
            """
            Internal function to start the scheduler job.
            This function calls the job_qs.py script.
            """
            # Stellt sicher, dass der Pfad zum Job-Skript korrekt ist
            job_path = os.path.join(workingdir, "jobs", 'job_qs.py')
            print(f"Starte Job: python {job_path}")
            os.system(f'python {job_path}')

        # Erstellt einen neuen Thread für die start_job-Funktion und startet ihn
        process = threading.Thread(target=start_job)
        process.start()
        print("Keyword Generation Controller launched.")


if __name__ == "__main__":
    # Initialisiert das KeywordController-Objekt
    keyword_controller = KeywordController()

    # Ermittelt das aktuelle Verzeichnis des Skripts
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    # Ermittelt das übergeordnete Verzeichnis
    parentdir = os.path.dirname(currentdir)

    # Bestimmt das Arbeitsverzeichnis. Annahme ist, dass sich das Skript im Hauptverzeichnis
    # oder einem Unterverzeichnis befindet und das 'jobs'-Verzeichnis im Hauptverzeichnis liegt.
    workingdir = parentdir if "controller" in currentdir else currentdir

    # Startet den Controller
    keyword_controller.start(workingdir)