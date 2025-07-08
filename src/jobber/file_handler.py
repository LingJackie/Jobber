import json
from pathlib import Path
from bs4 import BeautifulSoup


class FileHandler:
    """
    Handles general file I/O operations
    """
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent.parent

    def load_json(self, json_path):
        """
        Helper function for loading in json files

        :param json_path: String that contains the path of the json file
        :return: Spits out a dict of the json
        """ 
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: " + json_path + " not found.")
            return {"default": {}}
        except Exception as e:
            print(e)
            return {"default": {}}
        
    def load_job_app_selectors(self):
        """
        Loads selectors for job app webscraper
        """
        return self.load_json(self.base_dir / 'configs' / 'job_app_selectors.json')
    
    def load_resume_data(self, file_name: str):
        return self.load_json(self.base_dir / 'resources' / 'inputs' / 'resume_data' / file_name)
    
    def load_resume_template(self, file_name: str):
        try:
            with open(self.base_dir / 'resources' / 'inputs' / 'templates' / file_name, "r", encoding="utf-8") as f:
                return BeautifulSoup(f, "html.parser")
        except Exception as e:
            print("Error: Could not load template")
            return BeautifulSoup("", "html.parser")
        
    def write_to_html(self, parsed_html: BeautifulSoup, output_file: str):
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(str(parsed_html))
        except:
            print("Error: Unable to write file")
            
