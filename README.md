First part:
Getting the url's from the parquet file with pandas library an fastparquet engine and removing any duplicates
Function get favicon for each url, since some work with www. and some without I try them both
Use library fake_useragent for headrs to bypass anti scrapping methods and verify = false even if it's a security risk to disable SSL certificate verification and timeout = 5 to not keepp trying to reach the site
response = requests.get(url, headers = headers, verify = False, timeout = 5)
