import psycopg2, cv2, time, numpy as np

start_time = time.time()

def images_compare(img1_bytes, img2_bytes):
    try:

        nparr1 = np.frombuffer(img1_bytes, np.uint8)
        img1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
        
        nparr2 = np.frombuffer(img2_bytes, np.uint8)
        img2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

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

def cluster_domains():
    conn = psycopg2.connect(
        dbname="svg_storage",
        user="postgres",
        password="dlmvm",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    
    cursor.execute("SELECT domain, svg_data FROM favicons WHERE svg_data IS NOT NULL")
    all_domains = cursor.fetchall()
    

    cluster = {
        '100': [],
        '80': [],
        '50': [],
        'other': []
    }
    
    processed = set()
    
    def process_similarity(domain1, data1, domain2, data2, threshold):
        similarity = images_compare(data1, data2)
        if similarity >= threshold:
            return domain2
        return None
    
    # > 95%
    for i, (domain1, data1) in enumerate(all_domains):
        if domain1 in processed:
            continue
        current_group = [domain1]
        for j, (domain2, data2) in enumerate(all_domains[i+1:], start=i+1):
            result = process_similarity(domain1, data1, domain2, data2, 95)
            if result:
                current_group.append(result)
                processed.add(result)
        if len(current_group) > 1:
            cluster['100'].append(current_group)
            processed.add(domain1)
    
    # > 80%
    remaining = [d for d in all_domains if d[0] not in processed]
    
    for i, (domain1, data1) in enumerate(remaining):
        if domain1 in processed:
            continue
        current_group = [domain1]
        for j, (domain2, data2) in enumerate(remaining[i+1:], start=i+1):
            result = process_similarity(domain1, data1, domain2, data2, 80)
            if result:
                current_group.append(result)
                processed.add(result)
        if len(current_group) > 1:
            cluster['80'].append(current_group)
            processed.add(domain1)
    
    # > 50%
    remaining = [d for d in remaining if d[0] not in processed]
    
    for i, (domain1, data1) in enumerate(remaining):
        if domain1 in processed:
            continue
        current_group = [domain1]
        for j, (domain2, data2) in enumerate(remaining[i+1:], start=i+1):
            result = process_similarity(domain1, data1, domain2, data2, 50)
            if result:
                current_group.append(result)
                processed.add(result)
        if len(current_group) > 1:
            cluster['50'].append(current_group)
            processed.add(domain1)
    
    cluster['other'] = [d[0] for d in all_domains if d[0] not in processed]
    
    cursor.close()
    conn.close()
    
    return cluster

clusters = cluster_domains()

with open("output.txt", "w") as f:
    f.write("\nClustering Results:\n\n")
    f.write("\n---100% Similarity groups(95% - 100%)---\n\n")
    for group in clusters['100']:
        f.write(" ".join(group) + "\n")
        
    f.write("\n\n---Over 80% similarity groups---\n\n")
    for group in clusters['80']:
        f.write(" ".join(group) + "\n")
        
    f.write("\n\n---Over 50% similarity groups---\n\n")
    for group in clusters['50']:
        f.write(" ".join(group) + "\n")
        
    f.write("\n\n---Less than 50% similarity logos---\n\n")
    for domain in clusters['other']:
        f.write(domain + "\n")

elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"--- {int(minutes)} minutes and {int(seconds)} seconds ---")