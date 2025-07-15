import json
import logging
import base64
import re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class FileHandler:
    """
    Handles general file I/O operations
    Mainly used for loading configs and handling html files
    """
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent.parent
        self.output_dir = self.base_dir / 'resources' / 'outputs'
        self.input_dir = self.base_dir / 'resources' / 'inputs'

    def load_json(self, file_path: str) -> dict:
        """
        Helper function for loading in json files

        :param file_path: String that contains the path of the json file
        :return: Dictionary parsed from the JSON file
        """ 
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error("Unexpected error: ", e)
        return None
        
    def load_job_app_selectors(self) -> dict:
        """
        Loads selectors for job app webscraper
        """
        return self.load_json(self.base_dir / 'configs' / 'job_app_selectors.json')
    
    def load_resume_data(self, file_name: str) -> dict:
        """
        Loads resume data that is stored in a json
        """
        return self.load_json(self.base_dir / 'resources' / 'inputs' / 'resume_data' / file_name)
    
    def load_resume_template(self, file_name: str) -> BeautifulSoup:
        try:
            with open(self.base_dir / 'resources' / 'inputs' / 'templates' / file_name, "r", encoding="utf-8") as f:
                return BeautifulSoup(f, "html.parser")
        except Exception as e:
            logger.error("Could not load template: ", e)
            return BeautifulSoup("", "html.parser")
        
    def save_html(self, parsed_html: BeautifulSoup, output_path: str = None) -> bool:
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
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(parsed_html.prettify())
            return True
        except Exception as e:
            logger.error("Unable to write file: ", e)
        return False
           
    async def generate_pdf(self, dir_name: str, output_name: str = "Resume.pdf", input_name: str = "resume_wip.html") -> bool:
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
                    'marginBottom': 0 # Needs a value if you don't want text to ignore margins to overflow to next page (disregard if resume is 1 page long)
                })
                output_path = str(self.output_dir / dir_name / output_name)
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(pdf_data["data"]))
                await browser.close()
                return True
        except Exception as e:
            logger.error("Error generating PDF: ", e)
            return False
        
    async def print_length(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Load your local HTML file (replace with your actual file path or URL)
            await page.goto(str(self.base_dir / 'output.html'))

            # Evaluate scrollHeight of entire document
            scroll_height = await page.evaluate("document.documentElement.scrollHeight")
            print(f"Page ScrollHeight: {scroll_height}px")

            await browser.close()

    def sanitize_filename_and_directory(self, name: str) -> str:
        """
        Sanitizes a filename by removing invalid characters as well as newlines and carriage returns.
    
        :param name: The name to sanitize
        :return: Sanitized name
        """
        name = name.replace('\n', ' ').replace('\r', '') 
        return re.sub(r'[<>:"/\\|?*]', '', name)