import os, requests, pandas as pd, urllib3, time, psycopg2, cairosvg
from bs4 import BeautifulSoup
from PIL import Image, ImageChops
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed

from io import BytesIO

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

    except KeyboardInterrupt:
        print("\nInterrupted! Exiting...")
        exit(0)  # Force full stop

    except:
        return None
    

def download_convert_favicon(favicon_url):
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(favicon_url, headers = headers, stream=True, verify = False, timeout=5)
        response.raise_for_status()
        
        logo = Image.open(BytesIO(response.content))
        
        # Convert to byte array
        byte_arr = BytesIO()
        logo.save(byte_arr, format='PNG')
        byte_arr = byte_arr.getvalue()
        
        return byte_arr       

    
    except KeyboardInterrupt:
        print("\nInterrupted! Exiting...")
        exit(0)  # Force full stop
    except Exception as e:
        print(f"Error getting favicon: {e}")


def images_are_equal(img1, img2):
    return ImageChops.difference(img1, img2).getbbox() is None

def images_compare(img1, img2):
    diff = ImageChops.difference(img1, img2)
    diff_pixels = sum(sum(pixel) for pixel in diff.getdata())
    total_pixels = img1.size[0] * img1.size[1] * len(img1.getbands())
    percentage_diff = (diff_pixels / (total_pixels * 255)) * 100
    print(f"Difference: {percentage_diff:.2f}%")

def store_favicon_in_db(domain, svg_data):
    try:
        conn = psycopg2.connect(
            dbname="svg_storage",
            user="postgres",
            password="dlmvm",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Check if the image already exists in the database
        cursor.execute("SELECT svg_data FROM favicons")
        existing_images = cursor.fetchall()
        
        new_image = Image.open(BytesIO(svg_data))
        
        for existing_image_data in existing_images:
            existing_image = Image.open(BytesIO(existing_image_data[0]))
            if images_are_equal(new_image, existing_image):
                print("Already existing image")
                return
            else:
                print("Not equal")
                images_compare(new_image, existing_image)
        
        # If no match is found, insert the new image
        cursor.execute(
            "INSERT INTO favicons (domain, svg_data) VALUES (%s, %s) ON CONFLICT (domain) DO UPDATE SET svg_data = EXCLUDED.svg_data",
            (domain, svg_data)
        )
        conn.commit()
        cursor.close()
        conn.close()

    except KeyboardInterrupt:
        print("\nInterrupted! Exiting...")
        exit(0)  # Force full stop

    except Exception as e:
        print(f"Error storing favicon in database: {e}")

def fetch_favicon(domain):
    domain1 = 'https://www.' + domain
    domain2 = 'https://' + domain
    return get_favicon(domain1) or get_favicon(domain2)

num_cores = os.cpu_count()

print(f"Number of virtual cores: {num_cores}")

df = pd.read_parquet("logos.snappy.parquet", engine="fastparquet")
df.drop_duplicates(inplace=True)

# with ThreadPoolExecutor(max_workers = num_cores) as executor:
#     future_to_domain = {executor.submit(fetch_favicon, row['domain']): row['domain'] for index, row in df.iterrows()}
#     with open("output.txt", "w") as f:
#         for future in as_completed(future_to_domain):
#             domain = future_to_domain[future]
#             try:
#                 favicon_url = future.result()
#                 if favicon_url:
#                     f.write(f"{favicon_url}\n")
#                 else:
#                     f.write(f"Error fetching favicon for {domain}\n")
#             except Exception as e:
#                 f.write(f"Error fetching favicon for {domain}: {e}\n")


url = 'https://www.ovb.ro'
favicon_url = get_favicon(url)
print(favicon_url)
svg_data = download_convert_favicon(favicon_url)

store_favicon_in_db(url, svg_data)

elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"--- {int(minutes)} minutes and {int(seconds)} seconds ---")