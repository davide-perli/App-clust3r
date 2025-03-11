# Project Overview

## First Part

1. **Getting the URLs**:
   - Extract URLs from the parquet file using the pandas library with the fastparquet engine.
   - Remove any duplicates.

2. **Fetching Favicons**:
   - Implement a function to get the favicon for each URL.
   - After many tries and different approaches, I decided to use Google's free API: `https://www.google.com/s2/favicons?sz=64&domain_url=microsoft.com`. This solution was found on Stack Overflow.
   - Previous attempts included:
     - Using the BeautifulSoup library to parse the HTML and search links for keywords like "icon" or "logo". This approach usually gave me around 2966 - 3070 favicons because many sites update the logo or move it without taking the previous link down, so I often got an invalid link or worse, redirected to the main page.
     - Checking the link further for `raise_for_status() = 200` to check if the link was accessible and then checking the content type for an image type. This proved ineffective since if I needed to try other links, it would take time, and also multiple attempts to access some sites resulted in IP blocking with a 403 error (client forbidden) or 404/405 errors even when using the fake_useragent library.
     - Due to the lack of any VPN or proxy server for IP rotation to avoid being blocked, I attempted to use the Selenium library to utilize a headless browser, but it was a lot slower and still failed to get a lot of icons/logos from sites. Using the Tor browser instead would have been even slower.
   - Improvements using Google's free API:
     - Average time of 16 minutes and 20 seconds, whereas with BeautifulSoup (the second fastest), it took at least 29 minutes in the best cases.
     - 100% success at getting the icons/logos from the input example, whereas with BeautifulSoup (the second best), only around 87% of the icons/logos were obtained due to invalid file formats for the image or not getting the URL for the reasons mentioned previously (an attempt with retrial got me a little over 90%).
     - Got 3416 icons/logos out of 3416 (originally 4384, but there were duplicates eliminated with the command `df.drop_duplicates(inplace=True)`).

3. **Handling Anti-Scraping**:
   - Use the `fake_useragent` library for headers to bypass anti-scraping methods.
   - Set `verify=False` to disable SSL certificate verification (note: this is a security risk).
   - Set `timeout=10` to avoid long waits when trying to reach a site.
   - Example request:
     ```python
     response = requests.get(url, headers=headers, verify=False, timeout=10)
     ```

## Second Part

4. **Downloading and Converting the Icons/Logos**:
   - Open the URL where the icon/logo is located, check for the content type, verify and open it, and save it in a byte array for storage in the database and for later comparison.
   - Use the cairosvg library for SVG format and Pillow for the others.
   - Save the image as a byte array in PNG format.

5. **Comparing and Storing**:
   - Connect to the online database I created in PostgreSQL and pass the domain name and the image as a byte array.
   - Perform a fast byte comparison for exact duplicates (same domain URL and logo).
   - Store the data in the database.
   - Implement a comparison function between images using OpenCV format and histogram comparison (solution found online while searching for OpenCV documentation).

6. **Improving Performance**:
   - Since fetching favicons from all sites takes too long, use a ThreadPoolExecutor for parallelism on the task.
   - Utilize 20 virtual cores (with my CPU Intel I7 12700H) to achieve a 20x performance improvement.