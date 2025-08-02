import json
import logging
import base64
import re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import aiofiles
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class FileHandler:
    """
    Handles general file I/O operations
    Mainly used for loading configs and handling html files
    """
    def __init__(self, base_dir=None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.output_dir = self.base_dir / 'resources' / 'outputs'
        self.input_dir = self.base_dir / 'resources' / 'inputs'

    async def load_json_async(self, file_path: str) -> dict:
        """
        Helper function for loading in json files

        :param file_path: String that contains the path of the json file
        :return: Dictionary parsed from the JSON file
        """ 
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error("Unexpected error: ", e)
        return None
        
    async def load_job_app_selectors_async(self) -> dict:
        """Loads selectors for job app webscraper"""
        return await self.load_json_async(str(self.base_dir / 'configs' / 'job_app_selectors.json'))
    
    async def load_resume_data_async(self, file_name: str) -> dict:
        """Loads resume data that is stored in a json"""
        return await self.load_json_async(str(self.base_dir / 'resources' / 'inputs' / 'resume_data' / file_name))
    
    async def load_hotkey_config_async(self) -> dict:
        """Loads hotkey mappings from config"""
        return await self.load_json_async(str(self.base_dir / 'configs' / 'hotkeys_config.json'))

    async def load_resume_template_async(self, file_name: str) -> BeautifulSoup:
        """ 
        Loads a resume template from an HTML file
        :param file_name: Name of the HTML file to load
        :return: BeautifulSoup object containing the parsed HTML
        """
        try:
            template_path = str(self.base_dir / 'resources' / 'inputs' / 'templates' / file_name)
            async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return BeautifulSoup(content, "html.parser")
        except Exception as e:
            logger.error("Could not load template: %s", e)
            return BeautifulSoup("", "html.parser")
    
    async def save_html_async(self, parsed_html: BeautifulSoup, output_path: str = None) -> bool:
        """
        Saves a BeautifulSoup object as an HTML file
        :param parsed_html: BeautifulSoup object to save
        :param output_path: Optional path to save the HTML file. If None, uses a
        default path in the output directory.
        :return: True if the file was saved successfully, False otherwise
        """
        if output_path is None:
            output_path = str(self.output_dir / "resume_wip.html")
        try:
            async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
                await f.write(parsed_html.prettify())
            return True
        except Exception as e:
            logger.error("Unable to write file: %s", e)
        return False
           
    async def generate_pdf_async(self, dir_name: str, output_name: str = "Resume.pdf", input_name: str = "resume_wip.html") -> bool:
        """
        Generates a PDF from an HTML file using Chrome DevTools 
        :param dir_name: Directory name where the HTML file and pdf will be stored (Only the name, not the full path)
        :param output_name: Name of the output PDF file
        :param input_name: Name of the input HTML file
        :return: True if the PDF was generated successfully, False otherwise
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(str(self.output_dir / dir_name / input_name))

                # Connect to Chrome DevTools Protocol
                client = await context.new_cdp_session(page)

                # Trigger PDF generation
                pdf_data = await client.send("Page.printToPDF", {
                    "preferCSSPageSize": False,
                    'marginLeft': 0,
                    'marginRight': 0,
                    'marginTop': 0,
                    'marginBottom': 0 # Adjust >0 to add margins and prevent text overflow on pdf (If resume is a page long then ignore this)
                })
                output_path = str(self.output_dir / dir_name / output_name)
                async with aiofiles.open(output_path, "wb") as f:
                    await f.write(base64.b64decode(pdf_data["data"]))
                await browser.close()
                return True
        except Exception as e:
            logger.error("Error generating PDF: %s", e)
            return False
        
    async def print_length_async(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto(str(self.base_dir / 'output.html'))

            scroll_height = await page.evaluate("document.documentElement.scrollHeight")
            print(f"Page ScrollHeight: {scroll_height}px")

            await browser.close()

    
    
    def get_google_sheet_credentials(self):
        """
        Loads Google Sheets API credentials from a JSON file.
        :return: Credentials object
        """
        return str(self.base_dir / 'configs' / 'credentials.json')
    

    # [Output Directory Management]
    async def load_recent_output_dir_async(self) -> str:
        """
        Loads the most recent output directory from a JSON file
        :return: The most recent output directory name as a string
        """
        return await self.load_json_async(str(self.base_dir / 'configs' / 'recent.json'))
    
    def _sanitize_file_and_directory_name(self, name: str) -> str:
        """
        Sanitizes a filename by removing invalid characters as well as newlines and carriage returns.
    
        :param name: The name to sanitize
        :return: Sanitized name
        """
        name = name.replace('\n', ' ').replace('\r', ' ')
        return re.sub(r'[<>:"/\\|?*]', '', name)
    
    def _parse_timestamp(dir_name: str) -> datetime:
        """
        Extract datetime from dir name with format: yyyy-mmm-dd_hh-mm_name
        :param dir_name: Directory name to parse
        :return: Parsed datetime object or datetime.min if parsing fails
        """
        try:
            base = dir_name.split("_")[0:2]  # ['yyyy-mmm-dd', 'hh-mm']
            timestamp_str = "_".join(base)
            return datetime.strptime(timestamp_str, "%Y-%b-%d_%H-%M")
        except Exception:
            return datetime.min  # fallback if parsing fails
        
    def _slugify(self, text: str) -> str:
        """
        Converts a string into a slug format (lowercase, spaces replaced with dashes. E.g., "Software Engineer" -> "software-engineer").
        This is useful for creating directory names or file names that are URL-friendly
        :param text: input string
        :return: slugified string
        """ 
        if not text:
            return "n-a"
        return text.lower().replace(" ", "-").replace("_", "-")
    
    def _get_timestamp(self) -> str:
        """
        Returns the current timestamp in the format YYYY-MM-DD_HH-MM 
        Example: 2025-07-13_04-34
        """
        return datetime.now().strftime("%Y-%m-%d_%H-%M")
    
    def get_output_dir_name(self, company_name: str = "n-a", job_title: str = "n-a") -> str:
        """
        Create a new directory name with the format timestamp_companyname_title
        :param company_name: Name of the company
        :param job_title: Job title for the position
        :return: Formatted directory name (e.g., "2025-07-13_04-34_company-name_job-title")
        """ 
        formatted_company_name = self._sanitize_file_and_directory_name(company_name)
        formatted_company_name = self._slugify(formatted_company_name)
        formatted_job_title =    self._sanitize_file_and_directory_name(job_title)
        formatted_job_title =    self._slugify(formatted_job_title)
        return f"{self._get_timestamp()}_{formatted_company_name}_{formatted_job_title}"
    
    async def write_resume_to_html_async(self, parsed_template: BeautifulSoup, dir_name: str) -> bool :
        """
        Converts BeautifulSoup object into an html file and places its own directory based on the job posting and timestamp
        :param parsed_template: BeautifulSoup object containing the parsed HTML template
        :param dir_name: Directory name where the HTML file will be saved
        :return: True if the HTML file was saved successfully, False otherwise
        """ 
        output_dir = self.output_dir / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        file_name = "resume_wip.html"
        return await self.save_html_async(parsed_template, str(output_dir / file_name)) 
    


        