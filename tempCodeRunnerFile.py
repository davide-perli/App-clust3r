with ThreadPoolExecutor(max_workers = num_cores) as executor:
#     future_to_domain = {executor.submit(get_favicon, row[1]['domain']): row[1]['domain'] for row in df.iterrows()}

#     for future in as_completed(future_to_domain):
#         domain = future_to_domain[future]
#         try:
#             favicon_url = future.result()
#             if favicon_url:
#                 favicon_data = download_convert_favicon(favicon_url)

#                 if favicon_data:
#                     store_favicon_in_db(domain, favicon_data)
    
#                 else:
#                     j += 1
#                     continue
#             else:
#                 i += 1
#                 continue
                        
#         except Exception as e:
#             print(f"GETTING DOMAIN ERROR : {e} FOR {domain}")
#             continue