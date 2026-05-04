"""
Class to handle the resetting of failed or hanging Query Sampler (QS) jobs.

This script resets QS keywords and studies that are stuck in the processing 
state (status 2) back to pending (status 0).
"""

# Import required modules
import os
import inspect

# Import db library from the flask app
from db import reset_hanging_qs_jobs, get_keywords_bg

class QSReset:
    """
    Handles the resetting of hanging Query Sampler jobs.
    """

    def __init__(self):
        """
        Initializes the QSReset object.
        """
        pass

    def reset(self):
        """
        Resets the hanging QS jobs and checks for pending ones.
        """
        print("Checking for hanging Query Sampler jobs (status 2)...")
        
        # Reset stuck jobs back to 0
        reset_hanging_qs_jobs()
        print("Successfully reset hanging QS jobs to status 0.")

        # Check if there are still pending jobs (status 0) waiting to be processed
        pending_keywords = get_keywords_bg()
        if pending_keywords:
            print(f"INFO: There are currently {len(pending_keywords)} QS keywords pending (status 0).")
            print("If this number does not decrease, check your Google Ads API token in google-ads.yaml.")
        else:
            print("No pending QS keywords found. Everything is up to date.")

if __name__ == "__main__":
    """
    Main execution point for the QSReset script.
    """
    qs_reset = QSReset()
    qs_reset.reset()