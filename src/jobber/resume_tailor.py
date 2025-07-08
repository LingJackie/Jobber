from google import genai
from bs4 import BeautifulSoup
from job_post_scraper import JobPostScraper
from file_handler import FileHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO make use of gemini cache so I dont have to keep sending the resume
class ResumeTailor:
    def __init__(self, resume: dict, parsed_template: BeautifulSoup):
        """
        :param resume: dict containing resume data
        :param parsed_template: parsed resume template html
        """ 
        self.resume = resume
        self.parsed_template = parsed_template
        self.f_handler = FileHandler()
        self.scraper = JobPostScraper()

    def update_work_exp(self, updated_work_exp: dict) -> bool:
        """
        Updates resume dict's work experience section

        :param updated_work_exp: work experience that should be retrieved from LLM
        """ 
        old_work_exp = self.resume["data"]["work_experience"]
        if len(old_work_exp) != len(updated_work_exp):
            logger.error("Failed to update work history", exc_info=True)
            return False
        for old_exp, updated_exp in zip(old_work_exp, updated_work_exp):
            if old_exp["title"] == updated_exp["title"]:
                old_exp["responsibilities"] = updated_exp["responsibilities"]
        return True
            
    # TODO needs better error handling
    async def get_tailored_work_exp(self, job_desc: str):
        """
        Makes LLM tailor resume job descriptions based on the job posting

        :param job_desc: job description from job posting
        :return: LLM response which should be in json format
        """ 
        # only need the job title and descriptions from resume 
        extracted_exp = {
            key: {
                "title": value["title"],
                "responsibilities": value["responsibilities"]
            }
            for key, value in self.resume["data"]["work_experience"].items()
        }
        
        client = genai.Client() # The client gets the API key from the environment variable `GEMINI_API_KEY`
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents="You are a resume optimization assistant. I will give you a json containing my job title and a list of my job responsibilities along with a job posting description. " 
                                                    "Your job is to rewrite and select 5 bullet points per role that are most relevant to the job description. " 
                                                    "You are allowed to combine bullets as well. Format the rewrite in pure json, the same way as my job responsiblities. " 
                                                    "Do not include any markdown or explanations. Use double quotes"
                                                    "No periods. Here is my experience and the job app:" + str(extracted_exp) + job_desc
            )
            return response.text
        except:
            print("Unable to make request")
            return {
                "n/a": []
            }
        
    def populate_resume(self):
        """
        Adds data from self.resume into a soup

        :param job_desc: job description from job posting
        :return: LLM response which should be in json format
        """ 
        section = self.parsed_template.find(id="work-experience")

        # Inject each experience as a complete block
        for exp in self.resume["data"]["work_experience"].values():# TODO Placeholder
            table = self.parsed_template.new_tag("table", **{"class": "experience"})

            # table body
            tbody = self.parsed_template.new_tag("tbody")
            tr_left = self.parsed_template.new_tag("tr")
            tr_right = self.parsed_template.new_tag("tr")
            tbody.append(tr_left)
            tbody.append(tr_right)

            # job title and date
            title = self.parsed_template.new_tag("td", **{"class": "title"})
            title.string = exp["title"]
            date = self.parsed_template.new_tag("td", **{"class": "date"})
            date.string = f"{exp['start']} – {exp['end']}"
            tr_left.append(title)
            tr_left.append(date)

            # company and location
            company = self.parsed_template.new_tag("td", **{"class": "company"})
            company.string = exp["company"]
            location = self.parsed_template.new_tag("td", **{"class": "location"})
            location.string = exp["location"]
            tr_right.append(company)
            tr_right.append(location)

            # Bullet points
            ul = self.parsed_template.new_tag("ul", **{"class": "bullets"})
            for bullet in exp["responsibilities"]:
                li = self.parsed_template.new_tag("li")
                li.string = bullet
                ul.append(li)

            # Assemble and inject
            section.append(table)
            table.append(tbody)
            section.append(ul)

    def write_resume_to_html(self, file_name: str = "output.html"):
        self.f_handler.write_to_html(self.parsed_template, file_name) # TODO file name needs to be changed    

    def generate_tailored_resume(self):
        self.populate_resume()
        self.write_resume_to_html()


    # def infer_schema_from_example(self) -> dict:
    #     def get_type(val):
    #         if isinstance(val, str):
    #             return "string"
    #         elif isinstance(val, int):
    #             return "integer"
    #         elif isinstance(val, float):
    #             return "number"
    #         elif isinstance(val, bool):
    #             return "boolean"
    #         elif isinstance(val, list):
    #             return {
    #                 "type": "array",
    #                 "items": get_type(val[0]) if val else {}
    #             }
    #         elif isinstance(val, dict):
    #             return {
    #                 "type": "object",
    #                 "properties": {
    #                     k: get_type(v) for k, v in val.items()
    #                 }
    #             }
    #         else:
    #             return {}

    #     return {
    #         "type": "object",
    #         "properties": {
    #             key: get_type(value) for key, value in self.resume.items()
    #         },
    #         "required": list(self.resume.keys())
    #     }

    
    # def extract_json_block(self, text: str):
    #     """
    #     LLM response should be in the form of a json for easier parsing

    #     :param text: LLM text output
    #     :return: domain and extension string (Example: "myworkdayjobs.com")
    #     """ 
    #     start = text.find('{')
    #     end = text.rfind('}')
    #     result = text[start:end+1] if start != -1 and end != -1 else None

    