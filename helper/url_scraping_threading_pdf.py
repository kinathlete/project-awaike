import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import queue
import time
import os
import pdfkit
import shutil
import re
import tiktoken
# from weasyprint import HTML

# Configure pdfkit to use the binary
# config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

def convert_html_to_pdf(html_folder, pdf_folder):
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)

    # options = {
    #     'encoding': "UTF-8",
    #     'dpi': 400
    # }

    for html_file in os.listdir(html_folder):
        print(html_file)
        if html_file.endswith('.html'):
            html_path = os.path.join(html_folder, html_file)
            pdf_path = os.path.join(pdf_folder, html_file.replace('.html', '.pdf'))
            pdfkit.from_file(html_path, pdf_path)
            print(f"Converted {html_file} to PDF.")
    
    # return pdf file paths
    pdf_files = []
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith('.pdf'):
            pdf_files.append(os.path.join(pdf_folder, pdf_file))
    return pdf_files

# def convert_html_to_pdf(html_folder, pdf_folder):
#     if not os.path.exists(pdf_folder):
#         os.makedirs(pdf_folder)

#     for html_file in os.listdir(html_folder):
#         if html_file.endswith('.html'):
#             html_path = os.path.join(html_folder, html_file)
#             pdf_path = os.path.join(pdf_folder, html_file.replace('.html', '.pdf'))
            
#             # Using WeasyPrint to convert HTML to PDF
#             HTML(html_path).write_pdf(pdf_path)
#             print(f"Converted {html_file} to PDF.")

def get_all_links(base_url, visited_urls, lock, all_urls):
    try:
        r = requests.get(base_url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
    except requests.RequestException:
        return []

    links = soup.find_all('a')
    new_urls = []

    # Check if the base URL is a directory or a file
    if base_url.endswith('/'):
        base_dir = base_url
    else:
        base_dir = '/'.join(base_url.split('/')[:-1]) + '/'

    for link in links:
        href = link.get('href')
        if href and '#' not in href:
            # Construct the full URL based on the nature of the base URL
            if href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(base_dir, href)

            # Check if the full URL starts with the original base URL (or your desired scope)
            if full_url.startswith(base_dir):
                with lock:
                    if full_url not in visited_urls:
                        visited_urls.add(full_url)
                        all_urls.add(full_url)
                        new_urls.append(full_url)
    return new_urls

def get_text_from_url(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, 'html.parser')
    except requests.RequestException:
        return ""
    
    # Decompose (remove) unwanted sections
    for section in soup.find_all(['header', 'footer', 'aside', 'nav']):
        section.decompose()

    # Optional: Remove images
    for img in soup.find_all('img'):
        img.decompose()
    
    text_for_tokens = soup.get_text(separator=' ', strip=True)
    content = []
    
    url_header = f'<div class="url-header"><p>Source URL: <a href="{url}">{url}</a></p></div>'
    content.insert(0, url_header)
    
    # Collect remaining content
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'table']):
        element.attrs = {}
        for tag in element.find_all(True):
            tag.attrs = {}
        content.append(str(element))
        
    content.append('<hr>')

    combined_content = '\n'.join(content)

    # Clean non-printable characters
    clean_content = re.sub(r'[\x00-\x1f\x7f-\x9f\u200B]', '', combined_content)


    return clean_content,text_for_tokens


file_counter = 1
def save_to_html(all_htmls, folder_name):
    global file_counter
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    css_style = """
    <style>
        table { border-collapse: collapse; }
        td, th { border: 1px solid black; }
        th { border-bottom: 2px solid black; } /* Thicker bottom border for headers */
    </style>
    """   

    filename = os.path.join(folder_name, f"all_urls_part_{file_counter}.html")
    with open(filename, "w", encoding='utf-8') as file:
        styled_html = f"<html><head><meta charset='UTF-8'>{css_style}</head><body>"
        file.write(styled_html + "\n")
        for html in all_htmls:
            file.write(html + "\n")
        file.write("</body></html>")
        
    print(f"Saved {filename}")
    file_counter += 1  # Increment the counter

def delete_files_in_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"All files in '{folder}' have been deleted.")
    else:
        print(f"The folder '{folder}' does not exist.")


enc = tiktoken.encoding_for_model("gpt-4")
def calculate_token_count(text):
    return len(enc.encode(text))
        
def thread_function(url_queue, all_htmls, visited_urls, lock, processed_urls, token_limit, current_tokens, all_urls, html_folder):
    while True:
        try:
            current_url = url_queue.get(timeout=10)
        except queue.Empty:
            return

        new_links = get_all_links(current_url, visited_urls, lock, all_urls)
        with lock:
            for link in new_links:
                url_queue.put(link)
        

        html_data,text_data = get_text_from_url(current_url)
        if html_data:
            token_count = calculate_token_count(text_data)
            print(processed_urls[0],token_count, current_url)
            with lock:
                if current_tokens[0] + token_count >= token_limit:
                    # Save current batch before adding new content
                    save_to_html(all_htmls, html_folder)
                    all_htmls.clear()
                    current_tokens[0] = 0

                # Check if single URL content exceeds token limit
                if token_count >= token_limit:
                    # Handle large content separately
                    save_to_html([html_data], html_folder)
                else:
                    all_htmls.append(html_data)
                    current_tokens[0] += token_count

                processed_urls[0] += 1

def main(full_process, base_url):
    full_process = full_process  # Set this to False to only process the base URL
    base_url = base_url # 'https://developer.harness.io/docs/'
    visited_urls = set()
    all_urls = set()
    all_htmls = []
    processed_urls = [0]
    html_folder = 'html_files'
    pdf_folder = 'pdf_files'
    
    token_limit = 2000000
    current_tokens = [0]

    start_time = time.time()

    if full_process:
        # Full multi-threaded scraping and processing
        num_threads = 30
        threads = []
        lock = threading.Lock()
        num_pages = 1000

        url_queue = queue.Queue()
        url_queue.put(base_url)
        visited_urls.add(base_url)
        all_urls.add(base_url)

        for _ in range(num_threads):
            t = threading.Thread(target=thread_function, args=(url_queue, all_htmls, visited_urls, lock, processed_urls, token_limit, current_tokens, all_urls, html_folder))
            t.start()
            threads.append(t)

        while any(t.is_alive() for t in threads):
            time.sleep(5)

        if all_htmls:
            save_to_html(all_htmls, html_folder)
        

    else:
        # Only process the base URL
        html_data, abc = get_text_from_url(base_url)
        if html_data:
            save_to_html([html_data], html_folder)
    
    pdf_file_paths = convert_html_to_pdf(html_folder, pdf_folder)
    
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    
    print(len(all_urls))

    return pdf_file_paths

# if __name__ == "__main__":
#     main()