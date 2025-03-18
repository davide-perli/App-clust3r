import psycopg2, cv2, time, numpy as np, os
from concurrent.futures import ThreadPoolExecutor, as_completed

start_time = time.time()

num_cores = os.cpu_count()

print(f"Number of virtual cores: {num_cores}")

orb = cv2.ORB_create(
            nfeatures=500,  
            scaleFactor=1.3,  
            edgeThreshold=15  
        )

def images_compare(img1_bytes, img2_bytes):
    try:
        nparr1 = np.frombuffer(img1_bytes, np.uint8)
        img1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
        
        nparr2 = np.frombuffer(img2_bytes, np.uint8)
        img2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            return 0
        
        # standard_size = (64, 64)
        # img1 = cv2.resize(img1, standard_size)
        # img2 = cv2.resize(img2, standard_size)


        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)


        kpA, desA = orb.detectAndCompute(img1, None)
        kpB, desB = orb.detectAndCompute(img2, None)

        if len(kpA) < 10 or len(kpB) < 10:
            return 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        matches = bf.knnMatch(desA, desB, k=2)
        
        good_matches = []
        for m,n in matches:
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

        max_matches = min(len(kpA), len(kpB))
        if max_matches == 0:
            return 0
            
        similarity = (len(good_matches) / max_matches) * 100
        return min(similarity, 100)  

    except Exception as e:
        print(f"Comparison error: {e}")
        return 0

def cluster_domains():
    conn = psycopg2.connect(
        dbname = "svg_storage",
        user = "postgres",
        password = "dlmvm",
        host = "localhost",
        port = "5432"
    )
    cursor = conn.cursor()
    
    cursor.execute("SELECT domain FROM favicons WHERE is_no_logo = true")

    no_logo_domains = cursor.fetchall()

    cursor.execute("SELECT domain, svg_data FROM favicons WHERE is_no_logo = false")
    all_domains = cursor.fetchall()
    
    cluster = {
        '100': [],
        '80': [],
        '50': [],
        'other': [],
        'no_logo': []
    }

    cluster['no_logo'].extend([domain[0] for domain in no_logo_domains])
    
    processed = set()
    
    def process_similarity(domain1, data1, domain2, data2, threshold):
        if not data1 or not data2:
            return None
        similarity = images_compare(data1, data2)
        if similarity >= threshold:
            return domain2
        return None
    
    def cluster_domains_by_threshold(threshold, cluster_key):
        # Use only domains that haven't been processed
        remaining = [d for d in all_domains if d[0] not in processed]
        for i, (domain1, data1) in enumerate(remaining):
            if domain1 in processed:
                continue
            current_group = [domain1]
            with ThreadPoolExecutor(max_workers = num_cores) as executor:
                futures = {}
                for domain2, data2 in remaining[i+1:]:
                    if domain2 in processed:
                        continue
                    future = executor.submit(process_similarity, domain1, data1, domain2, data2, threshold)
                    futures[future] = domain2
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        current_group.append(result)
                        processed.add(result)
            if len(current_group) > 1:
                cluster[cluster_key].append(current_group)
                processed.add(domain1)

    cluster_domains_by_threshold(95, '100')
    cluster_domains_by_threshold(80, '80')
    cluster_domains_by_threshold(50, '50')

    remaining = [d for d in all_domains if d[0] not in processed]
    cluster['other'].extend([domain[0] for domain in remaining])
    
    cursor.close()
    conn.close()
    
    return cluster

clusters = cluster_domains()

with open("output.txt", "w") as f:
    f.write("\nClustering Results:\n\n")
    f.write("\n---95% - 100% Similarity groups (95% - 100%)---\n\n")
    for group in clusters['100']:
        f.write(" ".join(group) + "\n")
        
    f.write("\n\n---80% - 95% similarity groups---\n\n")
    for group in clusters['80']:
        f.write(" ".join(group) + "\n")
        
    f.write("\n\n---50% - 80% similarity groups---\n\n")
    for group in clusters['50']:
        f.write(" ".join(group) + "\n")
        
    f.write("\n\n---Less than 50% similarity logos---\n\n")
    for domain in clusters['other']:
        f.write(domain + "\n")

    f.write("\n\n---Sites with no logos/icons---\n\n")
    for domain in clusters['no_logo']:
        f.write(domain + "\n") 

elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"--- {int(minutes)} minutes and {int(seconds)} seconds ---")
#--- 39 minutes and 51 seconds ---