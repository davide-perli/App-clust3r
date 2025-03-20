# Introduction

## Summary

This project aims to match and group websites by the similarity of their logos

## Technologies used + interesting libraries/modules used

1. **Main and unique Technologies**

   - **Google's free API** for getting websites' logos/icons.

   - **PostgreSQL** database.

2. **Interesting libraries/modules used**

   - **OpenCV** -> for image processing and comparison using ORB feature detection algorithm.

   - **fake_useragent** -> to bypass anti-scraping websites.

   - **wand.image** -> to convert a `.svg` image to a `.png` one.

   - **mmap** -> memory mapping to access more efficiently the large no_logo image which is stored as bytes.

   - **ThreadPoolExecutor** -> to improve execution time by adding parallelism to the code.

# Project Overview

## Requirements

1. **Create a virtual environment**
   - Python 3.12.3 (other versions might work, but I haven't tested them).
   - Import the necessary modules listed in the `requirements.txt` file (link here: [requirements.txt](https://github.com/davide-perli/App-clust3r/blob/main/requirements.txt)) or install them using these commands:
     ```
     pip install requests pandas urllib3 psycopg2-binary opencv-python-headless numpy pillow fake-useragent beautifulsoup4 wand fastparquet
     ```

## Compilation

Run the `get_logo.py` program first.
Then run the `cluster_logo.py` program.
The list of URLs is stored in the `logos.snappy.parquet` file.
Results are saved in the `output.txt` file.
Connect to the database to store and view the URLs and the logos!
The results can be seen in the [output.txt file](https://github.com/davide-perli/App-clust3r/blob/main/output.txt)

## First Part

### 1. **Getting the URLs**

   - Extract URLs from the parquet file using the pandas library with the fastparquet engine.
   - Remove any duplicates.

### 2. **Fetching Favicons**

   - Implement a function to retrieve the favicon for each URL.
   - After many tries and different approaches, I decided to use Google's free API: `https://www.google.com/s2/favicons?sz=64&domain_url=microsoft.com`. This solution was found on Stack Overflow ([link](https://stackoverflow.com/questions/10456663/any-way-to-grab-a-logo-icon-from-website-url-programmatically)). I added various attempts like searching first with `https:\\url` then `https:\\www.` then `http:\\url` then `http:\\www.` and finally with BeautifulSoup to scrape the remaining ones parsing the HTML, looking for icons and logos in the links/src, prioritizing the ones with the `.png` extension. After each variant is tried, I check if it's similar to the no logo icon, and if it is, I try the next method and so on. As a fallback (I fail to get 36 icons/logos), I get the URL from the first use of the API (`https:\\`) and set the `is_no_logo` variable to `False` since it failed to get a logo/icon.

   - Previous attempts included:
     - Primarily using the BeautifulSoup library to parse the HTML and search links for keywords like "icon" or "logo". This approach usually gave me around 2966 - 3070 favicons because many sites update the logo or move it without taking the previous link down, so I often got an invalid link or, worse, redirected to the main page.
     - Checking the link further for `raise_for_status() = 200` to check if the link was accessible and then checking the content type for an image type. This proved ineffective since if I needed to try other links, it would take time, and also multiple attempts to access some sites resulted in IP blocking with a 403 error (client forbidden) or 404/405 errors even when using the `fake_useragent` library.
     - Due to the lack of any VPN or proxy server for IP rotation to avoid being blocked, I attempted to use the Selenium library to utilize a headless browser, but it was a lot slower and still failed to get a lot of icons/logos from sites. Using the Tor browser instead would have been even slower.

   - Improvements using Google's free API with BeautifulSoup as backup:
     - Best time of 22 minutes and 52 seconds; average time is around 23 minutes (depends on connection, internet speeds, processing power; these numbers are for my machine and may vary widely for others), whereas with only BeautifulSoup (the second fastest), it took at least 29 minutes in the best cases (for these measurements, the comparison function wasn't called, only implemented, and the clustering wasn't implemented).
     - 100% success at getting the icons/logos from the input example, whereas with BeautifulSoup (the second best), only around 87% of the icons/logos were obtained due to invalid file formats for the image or not getting the URL for the reasons mentioned previously (an attempt with a retry got me a little over 90%).
     - Got 3416 icons/logos out of 3416 (originally 4384, but there were duplicates eliminated with the command `df.drop_duplicates(inplace=True)`).
     - I wanted to distinguish the sites with no logo/icon from the other ones so they get grouped together in another category. After many tries, I found a solution. Resize the byte arrays to a 64x64 dimension (I know it takes up more storage, but it makes a more accurate comparison) and compare them with the byte array of a site with no logo/icon (the default planet-looking logo/icon) using the `images_compare` function from `cluster_logo.py`. If they match more than 98% (byte arrays may differ a little bit between each other), they are considered to have no logo/icon, and in the column "is_no_logo," which got added recently, is set to `True`; otherwise, it's `False` by default.
     - Using Google's API, a few sites got categorized as having no logo/icon even though they have one when manually checking without the API, but the results are still good, and it may be an issue on the site's fault.
     - Initially, I failed to get the logo/icon for 111 URLs, so I placed them in a dump.txt file to work only with them (sometimes I worked with only one until it was resolved). Using different URLs with Google's API (like "https://", "https://www.", "http://", "http://www.") and BeautifulSoup for further scraping of the sites, I managed to reduce the number to 36. Although this meant the program would run slower due to more comparisons and fetching more icons/logos.
     - Here is how it looks when a site doesn't have a logo/icon:

     ![alt text](image.png)

### 3. **Handling Anti-Scraping**

   - Use the `fake_useragent` library for headers to bypass anti-scraping methods.
   - Set `verify = False` to disable SSL certificate verification (note: this is a security risk).
   - Set `timeout = 10` to avoid long waits when trying to reach a site.
   - Example request:

     ```
     response = requests.get(url, headers={'User-Agent': UserAgent().random}, verify=False, timeout=10)
     ```

## Second Part

### 4. **Downloading and Converting the Icons/Logos**

   - Open the URL where the icon/logo is located, check for the content type, verify and open it, resize it, compare it to a byte array of the default logo/icon of a site which doesn't have one and determine if it has or not one, and save it in a byte array for storage in the database and for later comparison.
   - If it's a `.svg` format, convert it using the WandImage library (`cairosvg` failed for a couple) and remove `icc_profile` to get rid of `libpng warning: iCCP: known incorrect sRGB`.
   - Save the image as a byte array in PNG format.

### 5. **Comparing and Storing**

   - Connect to the online database I created in PostgreSQL and pass the domain name, the image as a byte array, and whether it has a logo/icon or not.
   - Store the data in the database.

### 6. **Improving Performance**

   - Since fetching favicons from all sites takes too long, use a `ThreadPoolExecutor` for parallelism on the task.
   - Utilize 20 virtual cores (with my CPU Intel I7 12700H) to achieve a 20x performance improvement.
   - Using a singleton class to implement the images compare function, read the byte array of the no logo image (also reading with `mmap` for a little boost in time) so that it's instantiated once, reuse it as much as needed since the orb creation and getting descriptors and matches for no logo needs to be done once as well as the brute force matcher using the Hamming norm. Instancing the class once and only pass in the `check_similarity` function inside the class the `byte_array` (image) to be compared to the no logo one.

## Third Part

### 7. **Fetching and Comparing Icons/Logos**

   - Use a cursor to fetch all the URLs and byte arrays and dump them in a list of tuples.
   - If the `is_no_logo` column is true, dump directly into a separate list composing only of the URLs.
   - Then process the similarity between each byte array (logos/icons of the sites).
   - Implement a comparison function between images using OpenCV format and histogram comparison at first, but then deciding on a feature-based method like the ORB algorithm. Also, resize the images for more accurate comparisons. Although slower (16 minutes histogram comparison vs. 30 minutes ORB), I find it more accurate since it covers transformations like rotation, scaling, and partial occlusion. Therefore, I find it better than pixel-based methods like histogram comparison or SSIM since spatial changes can be a factor when comparing logos/icons. I also improved the matching with a ratio test and applying Lowe's ratio test.
   - Based on the percentage of similarity (formula based on matches found / max matches of an image * 100), dump them in a dictionary where the keys are 5 different similarity options.
   - For each key, write the URLs grouped by similarity in an output text document by leaving a space between URLs.
   - Best time: 9 minutes and 8 seconds, but this greatly depends since the elements are dumped from the database in a list of tuples and then processed, which means that the whole data is kept in the RAM (I have 32GB) for processing until it is dumped in the output document. Because of this, time and performance may vary a lot. I also used `ThreadPoolExecutor` to improve speed (before I had 34 minutes since `ThreadPoolExecutor` doesn't create new threads but switches between tasks quicker so it) and add parallel processing.
   - In order to improve even more the execution times, the orb detector and brute force matcher are instantiated once and reused across multiple calls through singleton design pattern implementation instead of simply reusing the function with the parameters that need to be reinitialized for each call (could be initialized outside the function too).
   - All these improvements are meant to reduce execution time due to the fact that I have O(n^2) complexity since I compare each image with all the others and then remove it from the list and so on which is fine for 3416 images/logos but not that great for 20,000 for example. I believe working with image hashes might be better than with the image bytes scaled to 64x64, but it still doesn't remove the complexity.

## Results
   - The results can be seen in the [output.txt file](https://github.com/davide-perli/App-clust3r/blob/main/output.txt)
   - Total average time for processing all data in my case: 32 minutes
   - Amount of URLs processed: 4384, but 968 of them were exact duplicates so they were dropped immediately after opening the parquet
   - Number of failed icons/logos: 32 (of course some sites I couldn't get a logo/icon, but they are given one by default, the planet in shades of gray). This is due to the fact that I either couldn't process them or the fact that they changed the link for the logo leaving the old one behind which contained a blank white image, error 404 redirect pages, or redirect to the main page.
   - All of them were compared and grouped, but the comparison mode is subjective and not quite optimal since similarity can vary: similarity by color, shape, style, design, etc.
