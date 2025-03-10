import os, requests, pandas as pd, urllib3, time, psycopg2
from bs4 import BeautifulSoup
from PIL import Image, ImageChops
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
import cairosvg

from io import BytesIO

start_time = time.time()

# source enviroment/bin/activate

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_favicon(url):
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, verify=False, timeout=5)
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
        response = requests.get(favicon_url, headers=headers, stream=True, verify=False, timeout=5)
        
        # Check if response contains valid image data
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/') and content_type not in ['image/svg+xml', 'image/x-icon', 'image/avif']:
            print(f"Invalid content type for {favicon_url}")
            return None
            
        response.raise_for_status()
        
        # Handle SVG files
        if content_type == 'image/svg+xml':
            try:
                png_data = cairosvg.svg2png(bytestring=response.content)
                logo = Image.open(BytesIO(png_data))
            except Exception as e:
                print(f"Invalid SVG file: {favicon_url}")
                return None
        else:
            # Verify image can be opened
            try:
                logo = Image.open(BytesIO(response.content))
                logo.verify()  # Check image integrity
            except (IOError, OSError) as e:
                print(f"Invalid image file: {favicon_url}")
                return None
                
            # Re-open after verification
            logo = Image.open(BytesIO(response.content))
        
        # Handle transparency and color modes
        if logo.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', logo.size, (255, 255, 255))
            background.paste(logo, mask=logo.split()[-1])
            logo = background
            
        byte_arr = BytesIO()
        logo.save(byte_arr, format='PNG', optimize=True)
        return byte_arr.getvalue()

    except Exception as e:
        print(f"Error processing {favicon_url}: {str(e)}")
        return None


def images_are_equal(img1_bytes, img2_bytes):
    return img1_bytes == img2_bytes

def images_compare(img1_bytes, img2_bytes):
    try:
        # Convert bytes to OpenCV format
        nparr1 = np.frombuffer(img1_bytes, np.uint8)
        img1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
        
        nparr2 = np.frombuffer(img2_bytes, np.uint8)
        img2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

        # Resize and convert to HSV
        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

        # Histogram comparison
        hist1 = cv2.calcHist([hsv1], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [50, 60], [0, 180, 0, 256])
        
        cv2.normalize(hist1, hist1).flatten()
        cv2.normalize(hist2, hist2).flatten()
        
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL) * 100
    except Exception as e:
        print(f"Comparison error: {e}")
        return 0

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

        # Check for existing duplicates
        cursor.execute("SELECT domain, svg_data FROM favicons WHERE svg_data IS NOT NULL")
        existing = cursor.fetchall()
        
        duplicate = False
        reason = ""
        
        for existing_domain, existing_data in existing:
            if not existing_data:
                continue
                
            # Fast byte comparison
            if images_are_equal(svg_data, existing_data):
                reason = f"Exact duplicate of {existing_domain}"
                duplicate = True
                break

        if duplicate:
            print(f"Skipping {domain}: {reason}")
        elif svg_data:
            cursor.execute(
                """INSERT INTO favicons (domain, svg_data) 
                   VALUES (%s, %s) 
                   ON CONFLICT (domain) DO UPDATE SET 
                   svg_data = EXCLUDED.svg_data 
                   WHERE favicons.svg_data IS DISTINCT FROM EXCLUDED.svg_data""",
                (domain, svg_data)
            )
            conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Database error: {e}")


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
                favicon_data = download_convert_favicon(favicon_url)

                if favicon_data:
                    store_favicon_in_db(domain, favicon_data)
    
                else:
                    f.write(f"Error fetching favicon for {domain}\n")
            except Exception as e:
                f.write(f"Error fetching favicon for {domain}: {e}\n")


# url = 'https://www.enterprise.ae/'
# favicon_url = get_favicon(url)
#print(favicon_url)
# print(favicon_url)
# svg_data = download_convert_favicon(favicon_url)

# store_favicon_in_db(url, svg_data)

elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"--- {int(minutes)} minutes and {int(seconds)} seconds ---")

#Invalid image file: https://cafelasmargaritas.es/wp-content/uploads/2023/12/cropped-ico-32x32.avif