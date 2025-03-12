import os, requests, pandas as pd, urllib3, time, psycopg2
from PIL import Image
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
import cairosvg

from io import BytesIO

from pillow_avif import AvifImagePlugin

start_time = time.time()

# source enviroment/bin/activate

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_favicon(url, size = 64):
    try:
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url.lstrip("/")}'
            
        parsed = urlparse(url)
        domain = parsed.netloc.split(':')[0]
        return f"https://www.google.com/s2/favicons?domain={domain}&sz={max(16, min(256, size))}"
    
    except Exception as error:
        print(f"URL generation error: {error}")
        return f"https://www.google.com/s2/favicons?sz={size}"
    

def download_convert_favicon(favicon_url):
    try:
        headers = {'User-Agent': UserAgent().random}
        response = requests.get(favicon_url, headers = headers, verify = False, timeout = 10)
        content_type = response.headers.get('Content-Type', '')

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
                logo.verify() 
            except:
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
        logo.save(byte_arr, format = 'PNG', optimize = True)
        return byte_arr.getvalue()
    
    except Exception as e:
        print(f"Error processing {favicon_url}: {str(e)}")
        return None


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
            dbname = "svg_storage",
            user = "postgres",
            password = "dlmvm",
            host = "localhost",
            port = "5432"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT domain, svg_data FROM favicons WHERE svg_data IS NOT NULL")

        if svg_data:
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


num_cores = os.cpu_count()

print(f"Number of virtual cores: {num_cores}")

df = pd.read_parquet("logos.snappy.parquet", engine="fastparquet")
df.drop_duplicates(inplace=True)

i = 0
j = 0

with ThreadPoolExecutor(max_workers = num_cores) as executor:
    future_to_domain = {executor.submit(get_favicon, row[1]['domain']): row[1]['domain'] for row in df.iterrows()}

    for future in as_completed(future_to_domain):
        domain = future_to_domain[future]
        try:
            favicon_url = future.result()
            if favicon_url:
                favicon_data = download_convert_favicon(favicon_url)

                if favicon_data:
                    store_favicon_in_db(domain, favicon_data)
    
                else:
                    j += 1
                    continue
            else:
                i += 1
                continue
                        
        except Exception as e:
            print(f"GETTING DOMAIN ERROR : {e} FOR {domain}")
            continue


print(f"\nTotal number of failed url favicons: {i}")
print(f"\nTotal number of failed image downloads: {j}\n")

elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"--- {int(minutes)} minutes and {int(seconds)} seconds ---")