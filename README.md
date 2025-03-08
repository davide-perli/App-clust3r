# Project Overview

## First Part

1. **Getting the URLs**:
   - Extract URLs from the parquet file using the pandas library with the fastparquet engine.
   - Remove any duplicates.

2. **Fetching Favicons**:
   - Implement a function to get the favicon for each URL.
   - Since some URLs work with `www.` and some without, try both variations.

3. **Handling Anti-Scraping**:
   - Use the `fake_useragent` library for headers to bypass anti-scraping methods.
   - Set `verify=False` to disable SSL certificate verification (note: this is a security risk).
   - Set `timeout=5` to avoid long waits when trying to reach a site.
   - Example request:
     ```python
     response = requests.get(url, headers=headers, verify=False, timeout=5)
     ```

4. **Improving Performance**:
   - Since fetching favicons from all sites takes too long, use a thread pool for multithreading the task.
   - Utilize 20 virtual cores (in this case) to achieve 20x performance improvement.
