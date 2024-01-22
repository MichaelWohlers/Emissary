#business_info.py
import scrapy
from scrapy.http import Request
from scrapy.exceptions import IgnoreRequest
from scrapy import Spider, signals
import sqlite3
import os
import re
import logging
import time
from twisted.internet.error import DNSLookupError
from scrapy.spidermiddlewares.httperror import HttpError

# Set up a custom logger for errors
error_logger = logging.getLogger("error_logger")
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(filename='scraping_errors.log')
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_logger.addHandler(error_handler)


# Navigate up three levels to the 'leadGenerator' directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Now, append the 'instance' directory and the database file name
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'instance', 'places.db')


def fetch_urls_from_db():
    """Fetch URLs and their corresponding place_ids from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # Modify the SQL query to exclude places with 'Approved' or 'Blocked' status
    cursor.execute("SELECT id, website FROM place WHERE website IS NOT NULL AND status NOT IN ('Approved', 'Blocked')")
    url_to_place_id = {row[1]: row[0] for row in cursor.fetchall()}
    conn.close()
    return url_to_place_id


class BusinessInfoSpider(Spider):
    name = "business_info"

    def __init__(self, *args, **kwargs):
        super(BusinessInfoSpider, self).__init__(*args, **kwargs)

        # Set specific loggers' levels
        logging.getLogger('protego').setLevel(logging.INFO)
        logging.getLogger('scrapy.core.engine').setLevel(logging.WARNING)

        # Initialize progress tracking
        self.url_to_place_id = fetch_urls_from_db()
        self.total_urls = len(self.url_to_place_id)
        self.completed_urls = 0
        self.unprocessed_urls = set(self.url_to_place_id.keys())

        # Override the default logging method
        self.logger._log_original = self.logger._log
        self.logger._log = self._log_with_url

    def _log_with_url(self, level, *args, **kwargs):
        # Extract the URL from the request or response, if available
        url = None
        if 'request' in kwargs and kwargs['request']:
            url = kwargs['request'].url
        elif 'response' in kwargs and kwargs['response']:
            url = kwargs['response'].url

        # Append the URL to the log message, if it's available
        if url:
            args = (f"{args[0]}, URL: {url}",) + args[1:]

        # Call the original logging method
        self.logger._log_original(level, *args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BusinessInfoSpider, cls).from_crawler(crawler, *args, **kwargs)
        
        # Connect existing signal handlers
        crawler.signals.connect(spider.handle_spider_error, signal=signals.spider_error)

        # Connect the spider_closed method to the spider_closed signal
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)

        return spider
    
    
    def start_requests(self):
        for url, place_id in self.url_to_place_id.items():
            # Just use scrapy.Request without the 'endpoint' argument
            yield scrapy.Request(url, callback=self.parse, meta={'place_id': place_id})


    def parse(self, response):
        # Check for non-200 responses and log them
        if response.status != 200:
            self.logger.error(f'Non-200 response at {response.url}: {response.status}')
            # Handle redirects
            if response.status in [301, 302] and 'Location' in response.headers:
                new_url = response.headers['Location'].decode('utf-8')
                self.logger.info(f"Redirected to {new_url} from {response.url}")
                # Optionally follow the redirect manually
                return response.follow(new_url, self.parse, meta=response.meta)
            return

        page_text = response.xpath('//body//text()').getall()
        page_text = " ".join(page_text)

        email = self.extract_email(page_text, response)
        phone_number = self.extract_phone_number(page_text)

        if email or phone_number:
            contact_data = {
                'email': email,
                'phone_number': phone_number,
                'website': response.url
            }

            place_id = response.meta.get('place_id')
            if place_id is not None:
                self.save_contact_data(contact_data, place_id)
            else:
                self.logger.error(f"Missing place_id for the website: {response.url}")

            yield contact_data
        else:
            self.logger.info('Searching for Contact Pages')
            contact_links = self.find_contact_page_links(response)
            for link in contact_links:
                yield response.follow(link, self.parse_contact_page, meta={'place_id': response.meta['place_id']})
        
        self.unprocessed_urls.discard(response.url)
        self.update_progress()


    def parse_contact_page(self, response):
        # Log the URL of the contact page
        print(f"Accessing contact page: {response.url}")

        # Extracting contact information
        page_text = response.xpath('//body//text()').getall()
        page_text = " ".join(page_text)

        email = self.extract_email(page_text)
        phone_number = self.extract_phone_number(page_text)
        contact_name = self.extract_contact_name(response)
        contact_title = self.extract_contact_title(response)

        # Check if data is found and log accordingly
        if email or phone_number or contact_name or contact_title:
            print(f"Data found on contact page {response.url}: Email: {email}, Phone: {phone_number}, Name: {contact_name}, Title: {contact_title}")
        else:
            print(f"No contact data found on page: {response.url}")

        contact_data = {
            'email': email,
            'phone_number': phone_number,
            'contact_name': contact_name,
            'contact_title': contact_title,
        }

        place_id = response.meta.get('place_id')
        if place_id is not None:
            self.save_contact_data(contact_data, place_id)
        else:
            print(f"Missing place_id for the website: {response.url}")

        yield contact_data
        self.update_progress()

    # Implement the extraction logic here
    def extract_email(self, text, response):
        # First, try to extract email from 'mailto:' links
        mailto_emails = response.xpath('//a[contains(@href, "mailto:")]/@href').extract()
        for mailto in mailto_emails:
            email_match = re.search(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', mailto)
            if email_match:
                return email_match.group(1)

        # Fallback to searching the entire text using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            return emails[0]

        return None



    def extract_phone_number(self, text):
        phone_regex = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        match = re.search(phone_regex, text)
        return match.group(0) if match else None


    def extract_contact_name(self, response):
        return response.xpath('xpath_to_contact_name').get()

    def extract_contact_title(self, response):
        return response.xpath('xpath_to_contact_title').get()
    
    def is_valid_email(self, email):
        # Additional checks for email validation
        dummy_domains = ['example.com', 'mailinator.com', 'test.com']
        domain = email.split('@')[-1]
        if domain in dummy_domains or re.match(r'^[a-f0-9]{30,}@', email) or len(email) > 50:
            return False
        return True
    
    def save_contact_data(self, contact_data, place_id):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        try:
            email = contact_data.get('email')
            phone_number = contact_data.get('phone_number')
            contact_name = contact_data.get('contact_name')
            contact_title = contact_data.get('contact_title')

            if email and not self.is_valid_email(email):
                print(f"Invalid email detected: {email}. Skipping entry.")
                return

            cursor.execute("SELECT * FROM contact WHERE place_id = ?", (place_id,))
            existing_contact = cursor.fetchone()

            if existing_contact:
                # Update the existing contact
                update_data = {}
                if email and existing_contact[1] is None:
                    update_data['email'] = email
                if phone_number and existing_contact[2] is None:
                    update_data['phone_number'] = phone_number
                if contact_name and existing_contact[3] is None:
                    update_data['contact_name'] = contact_name
                if contact_title and existing_contact[4] is None:
                    update_data['contact_title'] = contact_title

                if update_data:
                    update_query = "UPDATE contact SET "
                    update_query += ', '.join([f"{k} = ?" for k in update_data.keys()])
                    update_query += " WHERE place_id = ?"
                    cursor.execute(update_query, list(update_data.values()) + [place_id])
                else:
                    print(f"No new data to update for place_id: {place_id}")
            else:
                # Insert a new contact
                cursor.execute("""
                    INSERT INTO contact (email, phone_number, contact_name, contact_title, place_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (email, phone_number, contact_name, contact_title, place_id))
                print(f"Saved new contact data for place_id: {place_id}")

            conn.commit()
        except Exception as e:
            print(f"Error in save_contact_data: {e}")
        finally:
            conn.close()


    def find_contact_page_links(self, response):
        contact_page_links = []
        for link in response.css('a'):
            url = link.xpath('@href').get()
            anchor_text = link.xpath('text()').get('').lower()
            if 'contact' in url.lower() or 'contact' in anchor_text:
                contact_page_links.append(url)
        return contact_page_links
                

    def update_progress(self):
        self.completed_urls += 1
        progress = (self.completed_urls / self.total_urls) * 100
        self.write_progress_to_file(progress)

    def write_progress_to_file(self, progress):
        # Function to write the progress to a file
        with open('progress.txt', 'w') as file:
            file.write(str(progress))

    
    def handle_spider_error(self, failure):
        response = getattr(failure.value, 'response', None)
        spider = getattr(failure.value, 'spider', self)

        # Enhanced logging for different error types
        if isinstance(failure.value, DNSLookupError):
            error_logger.error(f"DNS Lookup Error for URL: {failure.request.url}")
        elif isinstance(failure.value, HttpError):
            error_logger.error(f"HTTP Error {response.status} for URL: {response.url}")
        elif isinstance(failure.value, IgnoreRequest):
            error_logger.error(f"Request Ignored (possibly due to robots.txt): {failure.request.url}")
        else:
            error_logger.error(f"General Error encountered: {failure}")

        self.update_progress()

    

    def spider_closed(self, spider):
        # Log unprocessed URLs if any
        for url in self.unprocessed_urls:
            spider.logger.info(f"Unprocessed URL: {url}")
        # Ensure progress is set to 100% at the end
        self.write_progress_to_file(100)
        time.sleep(1.1)
        self.write_progress_to_file(0)
        
        
