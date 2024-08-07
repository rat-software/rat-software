# Config Files

The RAT-Backend applications use configuration files to connect to the database and initialize the backend for scraping.

## Setting Up the Configuration Files

1. **config_db.ini**
   - This file configures the connection to the RAT database, which uses PostgreSQL.
   
   ```
   [database]
   name = your_db        # Name of your database
   user = your_user      # Database user
   host = db_ip          # IP address of the database
   port = db_port        # Port of the database
   password = db_pass    # Database password
   ```

2. **config_sources.ini:**
   - This file configures the sources scraper to meet your needs.
   ```
   [scraper]
   wait_time = 5                 # Time in seconds that Selenium Driver waits before saving the content of a URL. A higher value increases the likelihood of scraping all content.
   debug_screenshots = 0         # Set to 1 to save screenshots of the scraping process for debugging; 0 to disable.
   timeout = 45                  # Maximum time in seconds before a scraping process is canceled.
   headless = 1                  # Set to 1 to enable headless mode (no browser UI), 0 to disable.
   job_server = your_job_server  # Name of the server where scraping occurs. Relevant if using multiple servers.
   refresh_time = 48             # Interval in hours to ensure sources are refreshed, preventing more than one scrape within 48 hours for similar queries or search engines.
   max_height = 50000            # Maximum height in pixels for scraping. Lower values speed up scraping but may result in incomplete content.
   min_width = 1024              # Minimum width in pixels for scraping.
   block_size = 500              # Size of scrolling blocks in pixels. Lower values result in slower scrolling but may capture more information.
   scroll_time = 2               # Time in seconds to pause scrolling. This accounts for slow-loading content by pausing at the end of each scrolling block.
   ```   