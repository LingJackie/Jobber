import asyncio
import re
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from timing import log
from file_handler import FileHandler


# api_key = os.getenv("GEMINI_API_KEY")
logger = logging.getLogger(__name__)


patterns = [
        
        r"At ([A-Z][\w&\-\s]+),",
        r"Join the team at ([A-Z][\w&\-\s]+?)\b",
        r"([A-Z][\w&\-\s]+?) is a (?:leading|fast-growing|well-known|top-tier)",
        r"([A-Z][\w&\-\s]+?) is an equal opportunity employer"
        # r"([A-Z][\w&\-\s]+?) is looking for",
    ]

class JobPostScraper:
    def __init__(self):
        self.job_title = "n/a"
        self.job_location = "n/a"
        self.job_salary = "n/a"
        self.job_description = "n/a"
        self.company_name = "n/a"

        self.f_handler = FileHandler()
        self.job_app_selector_dict = self.f_handler.load_job_app_selectors() # loads json containing a repository of site element selectors

    async def extract_job_data(self, page, selector_list: list):
        """
        Grabs innerHTML of page based on selectors

        :param page: playwright page
        :param selector_list: list of possible selectors for an element
        :return: innerHTML in the form of a string
        """ 
        for selector in selector_list:
            try:
                el = page.locator(selector).first
                text = await el.text_content(timeout=1500)
                if text and text.strip():
                    return text.strip()
            except:
                continue
        return None
    
    def get_domain_key(self, url: str) -> str:
        """
        Grabs the domain and extension. This is used elsewhere as a dict key for grabbing domain selectors

        :param url: site url
        :return: domain and extension (Example: "myworkdayjobs.com")
        """ 
        for domain in self.job_app_selector_dict:
            if domain in url:
                return domain
        return "default"
    
    def extract_company_name(self, text: str) -> str:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return "n/a"
    
    async def scrape_job_posting(self, url: str, max_retries: int = 3, delay: float = 2.0) -> bool:
        for attempt in range(1, max_retries + 1):
            browser = None
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, timeout=10000)

                    selector_list = self.job_app_selector_dict.get(self.get_domain_key(url))

                    if not selector_list:
                        logger.error(f"No selector list found")
                        return False

                    job_title_task = self.extract_job_data(page, selector_list["job_title"])
                    location_task  = self.extract_job_data(page, selector_list["job_loc"])
                    desc_task      = self.extract_job_data(page, selector_list["job_desc"])

                    job_title, job_location, job_description = await asyncio.gather(
                        job_title_task, location_task, desc_task
                    )

                    self.job_title = job_title
                    self.job_location = job_location
                    self.job_description = job_description
                    self.company_name = self.extract_company_name(self.job_description)

                    return True

            except PlaywrightTimeoutError:
                logger.warning(f"Timeout while navigating to {url} on attempt {attempt}")
            except Exception as e:
                logger.exception(f"Unexpected error while scraping {url} on attempt {attempt}: {e}")
            finally:
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        logger.warning("Failed to close browser cleanly")

            await asyncio.sleep(delay)

        logger.error(f"All attempts to scrape job posting at {url} have failed")
        return False





    