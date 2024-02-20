import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict

# 2 megabytes. average kindle e-book is 2.6 MB
MAX_URL_CONTENT_LENGTH = 2 * 5 * 1024 * 1024

# Q1 http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL
unique_pages = []

# Q2 Used to get 50 most common words
word_list = defaultdict(int)

# Q3 longest url and word count
longest_url = ('', 0)

# Q4  Map ics subdomains to number of unique pages detected in each subdomain
ics_subdomains = defaultdict(int)

# Map paths to times visited
visit_count = defaultdict(int)


# Read stop words from file
def get_stopwords(file_path, stop_words):
    with open(file_path) as file:
        stop_words.update(map(str.strip, file))

file_path = 'stopwords.txt'
STOP_WORDS = set()

get_stopwords(file_path, STOP_WORDS)



def scraper(url, resp):
    links = extract_next_links(url, resp)
    output_to_txt()
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    links = []

    if url in unique_pages:
        return links

    try:
        if resp.status == 200 and len(resp.raw_response.content) < MAX_URL_CONTENT_LENGTH:
            unique_pages.append(url)
            parse_url = urlparse(url)

            soup = BeautifulSoup(resp.raw_response.content, 'html.parser')


            try:
                tokens_list = tokenize_content(soup.text)

                if len(tokens_list) > 10:

                    global longest_url
                    if len(tokens_list) > longest_url[1]:
                        longest_url = (url, len(tokens_list))
                    for token in tokens_list:
                        word_list[token] += 1

                    parse_url = urlparse(url)

                    # reconstructed subdomain url. adds back https or http
                    subdomain_key = f"{parse_url.scheme}://{parse_url.netloc}"

                    if "ics.uci.edu" in parse_url.netloc:
                        ics_subdomains[subdomain_key] = ics_subdomains.get(subdomain_key, 0) + 1

            except Exception as e:
                print(f'Error extracting content from {url}: {e}')

            for new_url in soup.find_all('a'):
                # defragmented link
                absolute_url= urldefrag(urljoin(parse_url.scheme + "://" + parse_url.netloc, new_url['href']))[0]
                if '?' in absolute_url:
                    absolute_url = absolute_url.split("?")[0]
                if not max_visits(absolute_url):
                    links.append(absolute_url)
    except Exception as e:
        print(f'Error getting: {url}: {e}')

    return links


def is_valid(url):
    try:
        parsed = urlparse(url)
        pattern = re.compile(r"(?:http?://|https?://)?(?:\w+\.)?(?:ics|cs|informatics|stat)\.uci\.edu/")
        # pattern = re.compile(r'^https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)')

        if re.match(pattern, url.lower()):  # Checks if URL matches the requirements

            # Avoid pdfs and zip attachments
            if "zip-attachment" in parsed.path.lower():
                return False

            if "pdf" in parsed.path:
                return False

            return not re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico|php"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx|pps"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|ova"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv|xml"
                + r"|r|py|java|c|cc|cpp|h|svn|svn-base|bw|bigwig"
                + r"|txt|odc|apk|img|war"
                + r"|bam|bai|out|tab|edgecount|junction|ipynb|bib|lif"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        return False
    except TypeError:
        print("TypeError for ", parsed)
        raise


def tokenize_content(text):
    
    tokens = []
    for line in text.split('\n'):
        # lower case
        words = re.findall(r'[A-Za-z0-9]+(?:[\.\'\’\‘][A-Za-z0-9]+)*', line.lower())

        # filter out stop words and numbers
        words = [word for word in words if (word and len(word) > 1 and not word.isnumeric() and word not in STOP_WORDS)]
        tokens.extend(words)
    return tokens


# limits the amount of times a unique page can be visited to 10. Used instead of fingerprinting, simhash, etc
def max_visits(url):
    new_link = urldefrag(url)[0] if urldefrag(url)[0] else url
    if new_link not in visit_count:
        visit_count[new_link] = 1
    elif visit_count[new_link] < 10:
        visit_count[new_link] += 1
    else:
        return True
    return False


def output_to_txt():
    with open('output.txt', 'w', encoding='utf-8') as file:
        file.write("QUESTION #1" + "\n")
        file.write(f"Unique Pages: {len(unique_pages)}\n")
        for visited_url in unique_pages:
            file.write(visited_url + '\n')

        file.write("\nQUESTION #2" + "\n")
        file.write("\n50 Most Common Words:\n")
        sorted_words = sorted(word_list.items(), key=lambda x: x[1], reverse=True)

        for word, frequency in enumerate(sorted_words[:50], start=1):
            file.write(f"{word}: {frequency}\n")

        file.write("\nQUESTION #3" + "\n")
        file.write("\nLongest URL:\n")
        file.write(f"URL: {longest_url[0]}\n")
        file.write(f"Word Count: {longest_url[1]}\n")

        file.write("\nQUESTION #4" + "\n")
        file.write(f"\nSubdomains in the ics.uci.edu domain: {len(ics_subdomains)}\n")
        sorted_subdomains = sorted(ics_subdomains.items())
        for subdomain, count in sorted_subdomains:
            file.write(f"{subdomain}: {count}\n")
