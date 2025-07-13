import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup

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
        if output_path is None:
            output_path = str(self.output_dir)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(parsed_html.prettify())
            return True
        except Exception as e:
            logger.error("Unable to write file: ", e)
        return False
         
            
