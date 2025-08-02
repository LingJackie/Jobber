import asyncio
import re
import logging
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

from timing import log
from file_handler import FileHandler


# api_key = os.getenv("GEMINI_API_KEY")
logger = logging.getLogger(__name__)

"TODO: Account for iframes in job postings"

patterns = [
        r"At\s+([A-Z][\w\s&\-]+?)(?:,|\s|$)",
        r"Join the team at ([A-Z][\w&\-\s]+?)\b",
        r"([A-Z][\w&\-\s]+?) is a (?:leading|fast-growing|well-known|top-tier|global|premier|renowned|innovative|dynamic|reputable|established|trusted)",
        r"([A-Z][\w&\-\s]+?) is an equal opportunity employer",
        r"([A-Z][\w&\-\s]+?) is looking for",
    ]

class JobPostScraper:
    """
    Used to scrapes job postings from various job sites using Playwright
    """
    def __init__(self):
        self.job_title = "n-a"
        self.job_location = "n-a"
        self.job_salary = "n-a"
        self.job_description = "n-a"
        self.company_name = "n-a"
        
    @classmethod
    async def fetch_configs(cls):
        """
        Fetches the job app selectors from the file handler and initializes the JobPostScraper instance
        """
        instance = cls()
        instance.f_handler = FileHandler()
        instance.job_app_selector_dict = await instance.f_handler.load_job_app_selectors_async() # loads json containing a repository of site element selectors
        return instance
    
    async def _extract_job_data(self, page: Page, selector_list: list) -> str:
        contexts = [page]
        frame_elements = await page.locator("iframe").all()

        for frame_el in frame_elements:
            try:
                content_frame = await frame_el.content_frame()
                if content_frame:
                    contexts.append(content_frame)
            except Exception as e:
                logger.debug(f"⚠️ Could not get content frame: {e}")

        async def try_selectors_in_context(context):
            for selector in selector_list:
                try:
                    el = context.locator(selector).first
                    await el.wait_for(timeout=3000)
                    text = await el.text_content()
                    if text and text.strip():
                        text = text.replace('\n', ' ').replace('\r', '')
                        logger.debug(f"Selector: {selector} matched in {'iframe' if context != page else 'main page'} → {self._limit_string_with_ellipsis(text)}")
                        return text.strip()
                except Exception as e:
                    logger.debug(f"Selector failed in {'iframe' if context != page else 'main page'}: {selector} → {e}")
            return None

        results = await asyncio.gather(*[try_selectors_in_context(ctx) for ctx in contexts])
        for result in results:
            if result:
                return result

        logger.warning("No selectors yielded results (including iframes)")
        return "n-a"

    # async def _extract_job_data(self, page: Page, selector_list: list) -> str:
    #     """
    #     Tries selectors on the main page and then inside any iframe, returning first valid text match.

    #     :param page: playwright page
    #     :param selector_list: list of possible selectors for an element
    #     :return: innerHTML in the form of a string
    #     """
    #     contexts = [page]

    #     # Try adding iframe content frames if any
    #     frame_elements = await page.locator("iframe").all()
    #     for frame_el in frame_elements:
    #         try:
    #             content_frame = await frame_el.content_frame()
    #             if content_frame:
    #                 contexts.append(content_frame)
    #         except Exception as e:
    #             logger.debug(f"⚠️ Could not get content frame: {e}")

    #     for context in contexts:
    #         for selector in selector_list:
    #             try:
    #                 html = await context.content()
    #                 logger.debug(f"🔍 DOM snapshot for selector '{selector}': {html[:300]}...")

    #                 el = context.locator(selector).first
    #                 await el.wait_for(timeout=3000)
    #                 text = await el.text_content()
    #                 if text and text.strip():
    #                     text = text.replace('\n', ' ').replace('\r', '')
    #                     logger.debug(f"Selector: {selector} matched in {'iframe' if context != page else 'main page'} → {self._limit_string_with_ellipsis(text)}")
    #                     return text.strip()
    #             except Exception as e:
    #                 logger.debug(f"Selector failed in {'iframe' if context != page else 'main page'}: {selector} → {e}")

    #     logger.warning(f"No selectors yielded results (including iframes)")
    #     return "n-a"
    
    def _limit_string_with_ellipsis(self, s: str, max_length: int = 20) -> str:
        return s if len(s) <= max_length else s[:max_length - 3] + "..."
    
    def _get_domain_key(self, url: str) -> str:
        """
        Grabs the domain and extension. This is used elsewhere as a dict key for grabbing domain selectors

        :param url: site url
        :return: domain and extension (Example: "myworkdayjobs.com")
        """ 
        for domain in self.job_app_selector_dict:
            if domain in url:
                return domain
        return "default"
    
    def _extract_company_name(self, text: str) -> str:
        """
        Tries to extract the company's name from the job description

        :param text: job description
        :return: company's name
        """ 
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return "n-a"
    
    async def scrape_job_posting_async(self, url: str, max_retries: int = 3, delay: float = 2.0) -> bool:
        """
        Grabs job information from url and save it into class instance variables 

        :param url: sef explanatory
        :max_retries: # of retries to open url
        :delay: delay in seconds bewteen retries
        :return: True if successful
        """ 
        for attempt in range(1, max_retries + 1):
            browser = None
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=False)
                    page = await browser.new_page()
                    await page.goto(url, timeout=10000)

                    selector_list = self.job_app_selector_dict.get(self._get_domain_key(url))

                    if not selector_list:
                        logger.error(f"No selector list found")
                        return False

                    job_title_task = self._extract_job_data(page, selector_list["job_title"])
                    location_task  = self._extract_job_data(page, selector_list["job_loc"])
                    desc_task      = self._extract_job_data(page, selector_list["job_desc"])

                    job_title, job_location, job_description = await asyncio.gather(
                        job_title_task, location_task, desc_task
                    )

                    self.job_title          = job_title
                    self.job_location       = job_location
                    if job_description == "n-a":
                        return False
                    self.job_description    = job_description
                    self.company_name       = self._extract_company_name(self.job_description)
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





    