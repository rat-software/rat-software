# Chrome_Controller

The `chrome_controller` is designed to manage and terminate hanging Chrome and SeleniumBase processes. Occasionally, Selenium processes may not terminate properly, and this tool ensures that such processes are closed regularly.

## Starting the Chrome Controller

The application uses a Python background process scheduler to periodically check and terminate any unresponsive Chrome processes.

- **To Start the Application:**
   ```bash
   nohup python chrome_controller_start.py
    ```

- **To Stop the Application:**
    ```bash
    python chrome_controller_stop.py
    ```

- **Alternative Method:**
You can configure cron jobs to execute chrome_reset.py at regular intervals to manage the processes.
