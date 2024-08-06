# Export Scripts

The RAT-Frontend provides options for exporting study results. Additionally, we offer scripts to extend the methods for exporting results from the database, including sources as HTML and PNG files. To use these scripts, you need the study ID from which you wish to export the results. You can find the study ID in the `study` table of your PostgreSQL database.

## Available Export Scripts

1. **export_classifier_results**
   - Exports all results along with the results from all classifiers.
   - **Usage:**
     ```bash
     python export_classifier_results.py [study_id]
     ```

2. **export_results**
   - Exports all results from the database.
   - **Usage:**
     ```bash
     python export_results.py [study_id]
     ```

3. **export_sources**
   - Exports all sources from the database. The source code is saved as HTML, and the scraped screenshots are stored in the `export_sources/[study_id]` directory.
   - **Usage:**
     ```bash
     python export_sources.py [study_id]
     ```

Replace `[study_id]` with the ID of the study you want to export. Ensure that the study ID you provide is valid and exists in your database.
