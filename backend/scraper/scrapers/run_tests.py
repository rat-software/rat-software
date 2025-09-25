import os
import pytest
import datetime

# Directory for test files and reports
TEST_DIR = "tests"
REPORT_DIR = "reports"

# Timestamp for unique report filenames
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_file = f"test_report_{timestamp}.html"
report_path = os.path.join(REPORT_DIR, report_file)

# Find all relevant test files in TEST_DIR
test_files = [
    os.path.join(TEST_DIR, f)
    for f in os.listdir(TEST_DIR)
    if f.startswith("test_") and f.endswith(".py")
]

# Create the report directory if it doesn't exist
os.makedirs(REPORT_DIR, exist_ok=True)

# Run pytest with HTML report output
exit_code = pytest.main(test_files + [
    "--html=" + report_path,
    "--self-contained-html"
])

print(f"\nTest run completed. Report saved at: {report_path}")
exit(exit_code)
