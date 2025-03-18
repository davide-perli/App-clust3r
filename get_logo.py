import os, requests, pandas as pd, urllib3, time, psycopg2, cv2, numpy as np, mmap
from PIL import Image
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from bs4 import BeautifulSoup
from wand.image import Image as WandImage

start_time = time.time()

# source enviroment/bin/activate

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NoLogoComparer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NoLogoComparer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        with open("no_logo_byte_array_file.txt", "rb") as file:
            no_logo_byte_array = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        
        nparr2 = np.frombuffer(no_logo_byte_array, np.uint8)
        self.no_img = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)
        self.no_img_gray = cv2.cvtColor(self.no_img, cv2.COLOR_BGR2GRAY)
        
        self.orb = cv2.ORB_create(
            nfeatures=200,
            scaleFactor=1.3,
            edgeThreshold=15
        )
        self.kpB, self.desB = self.orb.detectAndCompute(self.no_img_gray, None)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    
    def check_similarity(self, img1_bytes):
        try:
            nparr1 = np.frombuffer(img1_bytes, np.uint8)
            img1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)

            if img1 is None:
                return 0

            img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            kpA, desA = self.orb.detectAndCompute(img1_gray, None)

            if len(kpA) < 10:
                return 0

            matches = self.bf.knnMatch(desA, self.desB, k=2)

            good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

            max_matches = min(len(kpA), len(self.kpB))
            if max_matches == 0:
                return 0

            similarity = (len(good_matches) / max_matches) * 100
            return min(similarity, 100)

        except Exception as e:
            print(f"Comparison error: {e}")
            return 0

no_logo_comparer = NoLogoComparer() # Instantiate the singleton

def check_no_logo(img1_bytes):
    return no_logo_comparer.check_similarity(img1_bytes)

def get_favicon_enhanced(url, size=64):
    try:     
        parsed_url = urlparse(url)
        query = parsed_url.query

        for param in query.split("&"):
            key, value = param.split("=")
            if key == "domain":
                domain = urlparse(value).netloc
                
        favicon_url = try_multiple_favicon_methods(domain, size)
        if favicon_url:
            return favicon_url
        else:
            return f"https://www.google.com/s2/favicons?domain={domain}&sz={max(16, min(256, size))}"
    except:
        return f"https://www.google.com/s2/favicons?domain={domain}&sz={max(16, min(256, size))}"


def try_multiple_favicon_methods(url, size=64):
    """Comprehensive logo/favicon discovery with img tag support."""
    
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url.lstrip("/")
    

    url_variants = [
        url,
        url.replace('http://', 'https://'),
        f'https://www.{url.split("://")[-1]}',
        f'http://www.{url.split("://")[-1]}'
    ]

    for variant in url_variants:
        response = requests.get(variant, headers={'User-Agent': UserAgent().random}, verify=False, timeout=10)
        if response.status_code == 200:
            break
    else:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    candidates = []
    icons = []

    logo_imgs = soup.find_all('img', {
        'src': lambda x: x and any(kw in x.lower() for kw in 'logo')
    })
    candidates.extend([urljoin(url, img['src']) for img in logo_imgs if img.get('src')])


    for link in candidates:
        if link:
            try:
                if any(link.lower().endswith(ext) for ext in '.png'):
                    return link
            except requests.RequestException:
                continue

    for rel in ['icon', 'shortcut icon', 'apple-touch-icon']:
        links = soup.find_all("link", rel=lambda x: x and rel in x.lower())
    candidates.extend([urljoin(url, l['href']) for l in links if l.get('href')])
    icons.extend([urljoin(url, l['href']) for l in links if l.get('href')])
    

    for link in icons:
        if link:
            try:
                if any(link.lower().endswith(ext) for ext in '.png'):
                    return link
            except requests.RequestException:
                continue

    for link in candidates:
        if link:
            try:
                if any(link.lower().endswith(ext) for ext in ['.ico', '.avif', '.svg', '.jpeg', '.jpg']):
                    return link
            except requests.RequestException:
                continue
    return None




def get_favicon_no_secure_protocol_www(url, size=64):
        
    parsed_url = urlparse(url)
    query = parsed_url.query

    for param in query.split("&"):
        key, value = param.split("=")
        if key == "domain":
            domain = "www." + urlparse(value).netloc
    url = domain
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url.lstrip("/")
    
    return f"https://www.google.com/s2/favicons?domain={domain}&sz={max(16, min(256, size))}"


def get_favicon_no_secure_protocol(url, size=64):
  
    parsed_url = urlparse(url)
    query = parsed_url.query

    for param in query.split("&"):
        key, value = param.split("=")
        if key == "domain":
            domain = urlparse(value).netloc
    url = domain
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url.lstrip("/")
    
    return f"https://www.google.com/s2/favicons?domain={domain}&sz={max(16, min(256, size))}"
    

def get_favicon_www(url, size=64):
      
    parsed_url = urlparse(url)
    query = parsed_url.query

    for param in query.split("&"):
        key, value = param.split("=")
        if key == "domain":
            domain = "www." + urlparse(value).netloc
    url = domain
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url.lstrip("/")
    
    return f"https://www.google.com/s2/favicons?domain={domain}&sz={max(16, min(256, size))}"



def get_favicon(url, size = 64):

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url.lstrip("/")
        
    return f"https://www.google.com/s2/favicons?domain={url}&sz={max(16, min(256, size))}"

    

def download_convert_favicon(favicon_url):
    try:
        headers = {'User-Agent': UserAgent().random}
        response = requests.get(favicon_url, headers = headers, verify = False, timeout = 10)

        try:
            logo = Image.open(BytesIO(response.content))
            logo.verify() 
        except:
            print(f"Invalid image file: {favicon_url}")
            return None
            
        logo = Image.open(BytesIO(response.content))
        logo = logo.resize((64, 64), Image.LANCZOS)
            
        byte_arr = BytesIO()
        logo.save(byte_arr, format = 'PNG', optimize = True)
        favicon_data = byte_arr.getvalue()
        backup_favicon_data = favicon_data
    
        similarity = check_no_logo(favicon_data)
        if similarity > 99:
            url = favicon_url
            methods = [get_favicon_www, get_favicon_no_secure_protocol, get_favicon_no_secure_protocol_www]
            for attempt in methods:
                favicon_url = attempt(url)
                response = requests.get(favicon_url, headers = {'User-Agent': UserAgent().random}, verify = False, timeout = 10)

                logo = Image.open(BytesIO(response.content))
                logo.verify() 
                
                logo = Image.open(BytesIO(response.content))
                logo = logo.resize((64, 64), Image.LANCZOS)
                
                byte_arr = BytesIO()
                logo.save(byte_arr, format = 'PNG', optimize = True)


                favicon_data = byte_arr.getvalue()
                similarity = check_no_logo(favicon_data)
                if similarity < 99: 
                    return favicon_data, False
            else:
                favicon_url = get_favicon_enhanced(url)
                response = requests.get(favicon_url, headers = {'User-Agent': UserAgent().random}, verify = False, timeout = 10)
                
                # Handle SVG files
                if 'svg' in response.headers.get('Content-Type', ''):
                    try:
                        # Convert SVG to PNG using Wand
                        with WandImage(blob = response.content) as img:
                            img.strip()
                            img.format = 'png'
                            png_data = img.make_blob()

                        logo = Image.open(BytesIO(png_data))
                        logo.info.pop('icc_profile', None)

                        logo = logo.convert("RGBA")

                        logo = logo.resize((64, 64), Image.LANCZOS)

                        byte_arr = BytesIO()
                        logo.save(byte_arr, format = 'PNG', optimize = True, icc_profile = None)
                        byte_arr.seek(0) 

                        logo = Image.open(byte_arr) 
                        logo = logo.resize((64, 64), Image.LANCZOS)

                        byte_arr = BytesIO()
                        logo.save(byte_arr, format = 'PNG', optimize = True)
                        favicon_data = byte_arr.getvalue()
                        similarity = check_no_logo(favicon_data)

                        is_no_logo = similarity > 99
                        return favicon_data, is_no_logo

                    except Exception as e:
                        print(f"An error occurred: {e}")

                else:
                    try:
                        logo = Image.open(BytesIO(response.content))
                        logo.verify()
                    except:
                        is_no_logo = True
                        return backup_favicon_data, is_no_logo
                    
                logo = Image.open(BytesIO(response.content))
                logo = logo.resize((64, 64), Image.LANCZOS)
                    
                byte_arr = BytesIO()
                logo.save(byte_arr, format = 'PNG', optimize = True, icc_profile = None)
                byte_arr.seek(0) 

                logo = Image.open(byte_arr) 
                logo = logo.resize((64, 64), Image.LANCZOS)

                byte_arr = BytesIO()
                logo.save(byte_arr, format = 'PNG', optimize = True)

                favicon_data = byte_arr.getvalue()
                similarity = check_no_logo(favicon_data) 
                is_no_logo = similarity > 99
                return favicon_data, is_no_logo
            
        return favicon_data, False
    
    except Exception as e:
        #print(f"ERROR: {e}")
        is_no_logo = True
        return favicon_data, is_no_logo

def store_favicon_in_db(domain, svg_data, is_no_logo):
    try:
        conn = psycopg2.connect(
            dbname = "svg_storage",
            user = "postgres",
            password = "dlmvm",
            host = "localhost",
            port = "5432"
        )
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO favicons (domain, svg_data, is_no_logo) 
               VALUES (%s, %s, %s) 
               ON CONFLICT (domain) DO UPDATE SET 
               svg_data = EXCLUDED.svg_data,
               is_no_logo = EXCLUDED.is_no_logo 
               WHERE favicons.svg_data IS DISTINCT FROM EXCLUDED.svg_data""",
            (domain, svg_data, is_no_logo)
        )
        conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Database error: {e}")



num_cores = os.cpu_count()

print(f"Number of virtual cores: {num_cores}")

df = pd.read_parquet("logos.snappy.parquet", engine = "fastparquet")
df.drop_duplicates(inplace = True)

# with open("dump.txt", "r") as file:
#     lines = file.readlines()

# # Create a DataFrame from the lines
# df = pd.DataFrame(lines, columns=["domain"])


i = 0
j = 0

with ThreadPoolExecutor(max_workers = num_cores) as executor:
    future_to_domain = {executor.submit(get_favicon, row[1]['domain']): row[1]['domain'] for row in df.iterrows()}

    for future in as_completed(future_to_domain):
        domain = future_to_domain[future]
        try:
            favicon_url = future.result()
            if favicon_url:
                favicon_data, is_no_logo = download_convert_favicon(favicon_url)

                if favicon_data:
                    store_favicon_in_db(domain, favicon_data, is_no_logo)
    
                else:
                    j += 1
                    continue
            else:
                i += 1
                continue
                        
        except Exception as e:
            print(f"GETTING DOMAIN ERROR : {e} FOR {domain}")
            continue
# chicco.pl
#
# url = "bbraun.ae"
# url = "bbraun.pe"
# #print(f"{get_favicon(url)}")
# print(f"{download_convert_favicon(get_favicon(url))}")



print(f"\nTotal number of failed url favicons: {i}")
print(f"\nTotal number of failed image downloads: {j}\n")

elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"--- {int(minutes)} minutes and {int(seconds)} seconds ---")
#--- 22 minutes and 52 seconds ---