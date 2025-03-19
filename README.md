# Project Overview

## Requirements

1. **Create a virtual enviroment**
   -> Import the  needed modules listed in the requirements.txt (link here: [requirements.txt]())

## Compilation

Run the `get_logo.py` program first.  
Then run the `cluster_logo.py` program.  
The list of URLs is kept in the `logos.snappy.parquet` file.  
Results are put in the `output.txt` file.  
Connect to the database to store/see the URLs and the logos!

## First Part

1. **Getting the URLs**:
   - Extract URLs from the parquet file using the pandas library with the fastparquet engine.
   - Remove any duplicates.

2. **Fetching Favicons**:
   - Implement a function to get the favicon for each URL.
   - After many tries and different approaches, I decided to use Google's free API: `https://www.google.com/s2/favicons?sz=64&domain_url=microsoft.com`. This solution was found on Stack Overflow ([link](https://stackoverflow.com/questions/10456663/any-way-to-grab-a-logo-icon-from-website-url-programmatically)). I added various attempts like searching first with `https:\\url` than `https:\\wwww.` than `http:\\` than `http:\\www.` and finally with BeautifulSoup to scrape the remainder ones parsing the html looking for icons and logos in the links/src with priority on the ones with the extension `.png`. After each variant is tried I check if it's similar with the no logo icon and if it is I try the next method and so on and as a fallback (I fail to get 33 icons/logos) I get the url from the first use of the API (https:\\) and set is_no_logo variable to False since it failed to get a logo/icon
   - Previous attempts included:
     - Primarly using the BeautifulSoup library to parse the HTML and search links for keywords like "icon" or "logo". This approach usually gave me around 2966 - 3070 favicons because many sites update the logo or move it without taking the previous link down, so I often got an invalid link or worse, redirected to the main page.
     - Checking the link further for `raise_for_status() = 200` to check if the link was accessible and then checking the content type for an image type. This proved ineffective since if I needed to try other links, it would take time, and also multiple attempts to access some sites resulted in IP blocking with a 403 error (client forbidden) or 404/405 errors even when using the fake_useragent library.
     - Due to the lack of any VPN or proxy server for IP rotation to avoid being blocked, I attempted to use the Selenium library to utilize a headless browser, but it was a lot slower and still failed to get a lot of icons/logos from sites. Using the Tor browser instead would have been even slower.
   - Improvements using Google's free API:
     - Best time of 22 minutes and 52 seconds, average time is around 23 minutes (depends on connection, internet speeds, processing power; these numbers are for my machine and may vary widely for others), whereas with BeautifulSoup (the second fastest), it took at least 29 minutes in the best cases (for these measurements the comparison function wasn't called, only implemented, and the clustering wasn't implemented).
     - 100% success at getting the icons/logos from the input example, whereas with BeautifulSoup (the second best), only around 87% of the icons/logos were obtained due to invalid file formats for the image or not getting the URL for the reasons mentioned previously (an attempt with retrial got me a little over 90%).
     - Got 3416 icons/logos out of 3416 (originally 4384, but there were duplicates eliminated with the command `df.drop_duplicates(inplace=True)`).
     - I wanted to distinguish the sites with no logo/icon from the other ones so they get grouped together in another category. After many tries, I found a solution. Resize the byte arrays to a 64x64 dimension (I know it takes up more storage but it makes a more accurate comparison) and compare them with the byte array of a site with no logo/icon (the default planet-looking logo/icon) using the `images_compare` function from `cluster_logo.py` and if they match more than 98% (byte arrays may differ a little bit between each other) they are considered to have no logo/icon and in the column "is_no_logo" which got added recently is set to true, otherwise it's false by default.
     - Using Google's API a few sites got categorized as having no logo/icon even though they have one when manually checking without the API, but the results are still good and it may be an issue on the site's fault.
     - Here is how it looks when a site doesn't have a logo/icon:
     
     ![alt text](image.png)

3. **Handling Anti-Scraping**:
   - Use the `fake_useragent` library for headers to bypass anti-scraping methods.
   - Set `verify = False` to disable SSL certificate verification (note: this is a security risk).
   - Set `timeout = 10` to avoid long waits when trying to reach a site.
   - Example request:
     ```python
     response = requests.get(url, headers = {'User-Agent': UserAgent().random}, verify = False, timeout = 10)
     ```

## Second Part

4. **Downloading and Converting the Icons/Logos**:
   - Open the URL where the icon/logo is located, check for the content type, verify and open it, resize it, compare it to a byte array of the default logo/icon of a site which doesn't have one and determine if it has or not one and save it in a byte array for storage in the database and for later comparison.
   - If it's a `.svg` format convert it using WandImage library (cairosvg failed for a couple) and remove icc_profile to get rid of `libpng warning: iCCP: known incorrect sRGB`.
   - Save the image as a byte array in PNG format.

5. **Comparing and Storing**:
   - Connect to the online database I created in PostgreSQL and pass the domain name, the image as a byte array and if it has a logo/icon or not.
   - Store the data in the database.

6. **Improving Performance**:
   - Since fetching favicons from all sites takes too long, use a ThreadPoolExecutor for parallelism on the task.
   - Utilize 20 virtual cores (with my CPU Intel I7 12700H) to achieve a 20x performance improvement.
   - Using a singleton class to implement the images compare function, read the byte array of the no logo image (also reading with mmap for a little boost in time) so that it's instanced once, reuse it as much as needed since the orb creation and getting descriptors and matches for no logo needs to be done once as well as the brute force matcher using the Hamming norm. Instancing the class once and only pass in the check_similarity function inside the class the byte_array(image) to be compared to the no logo one.

## Third Part

7. **Fetching and Comparing Icons/Logos**:
   - Use a cursor to fetch all the URLs and byte arrays and dump them in a list of tuples.
   - If the `is_no_logo` column is true, dump directly in a separate list composing only of the URLs.
   - Then process the similarity between each byte array (logos/icons of the sites).
   - Implement a comparison function between images using OpenCV format and histogram comparison at first, but then deciding on a feature-based method like the ORB algorithm. Also resize the images for more accurate comparisons. Although slower (16 minutes histogram comparison vs 30 minutes ORB), I find it more accurate since it covers transformations like rotation, scaling, and partial occlusion. Therefore, I find it better than pixel-based methods like histogram comparison or SSIM since spatial changes can be a factor when comparing logos/icons. I also improved the matching with a ratio test and applying Lowe's ratio test.
   - Based on the percentage of similarity (formula based on matches found / max matches of an image * 100), dump them in a dictionary where the keys are 5 different similarity options.
   - For each key, write the URLs grouped by similarity in an output text document by leaving a space between URLs.
   - Average time: 9 minutes, but this greatly depends since the elements are dumped from the database in a list of tuples and then processed, which means that the whole data is kept in the RAM (I have 32GB) for processing until it is dumped in the output document. Because of this, time and performance may vary a lot. I also used `ThreadPoolExecutor` to improve speed (before I had 34 minutes since ThreadPoolExecutor doesn't create new threads but switches between tasks quicker so it) and add parallel  processing.
   - In order to improve even more the execution times the orb detector and brute force matcher are instantiated once and reused across multiple calls through singleton design pattern implementation instead of simply reusing the function with the parameters that need to be reinitialized for each call (could be initialized outside the function too).
   - All these improvements are meant to reduce execution time due to the fact that I have O(n^2) complexity since I compare each image with all the others and then remove it from the list and so on which is fine for 3416 images/logos but not that great for 20.000 for example since most exponential algorithms are not that scalable. I believe working with image hashes might be better than with the image bytes scaled to 64x64, but it still doesn't remove the complexity.


## Results
   - Total average time for processing all data in my case: 32 minutes
   - Amount of URLs processed: 4384, but 968 of them were exact duplicates so they were dropped immediately after opening the parquet
   - Number of failed icons/logos: 0 (of course some sites didn't have a logo, but they are given one by default, the planet in shades of gray).
   - All of them were compared and grouped, but the comparison mode is subjective and not quite optimal since similarity can vary: similarity by color, shape, style, design, etc.