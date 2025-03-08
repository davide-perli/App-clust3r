import os, requests, pandas as pd, urllib3, time, cv2
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed

start_time = time.time()

# source enviroment/bin/activate

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_favicon(url):
    try:

        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers = headers, verify = False, timeout = 5)
        response.raise_for_status()

        # Parse the HTML to find <link rel="icon" or rel="shortcut icon">
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.find("link", rel=lambda x: x and "icon" in x)

        # Return the href attribute if found, otherwise fallback to /favicon.ico
        if link and link.get('href'):
            return urljoin(url, link.get('href'))
        else:
            return f"{urlparse(url).scheme}://{urlparse(url).netloc}/favicon.ico"

    # except KeyboardInterrupt:
    #     print("\nInterrupted! Exiting...")
    #     exit(0)  # Force full stop

    except:
        return None

def fetch_favicon(domain):
    domain1 = 'https://www.' + domain
    domain2 = 'https://' + domain
    return get_favicon(domain1) or get_favicon(domain2)

num_cores = os.cpu_count()

print(f"Number of virtual cores: {num_cores}")

df = pd.read_parquet("logos.snappy.parquet", engine="fastparquet")
df.drop_duplicates(inplace=True)

with ThreadPoolExecutor(max_workers = num_cores) as executor:
    future_to_domain = {executor.submit(fetch_favicon, row['domain']): row['domain'] for index, row in df.iterrows()}
    with open("output.txt", "w") as f:
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                favicon_url = future.result()
                if favicon_url:
                    f.write(f"{favicon_url}\n")
                else:
                    f.write(f"Error fetching favicon for {domain}\n")
            except Exception as e:
                f.write(f"Error fetching favicon for {domain}: {e}\n")


elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"--- {int(minutes)} minutes and {int(seconds)} seconds ---")
