import logging
import json
import asyncio
from google import genai
from bs4 import BeautifulSoup
from job_post_scraper import JobPostScraper
from file_handler import FileHandler
from httpx import TimeoutException, RequestError


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
    def parse_work_experience(self, payload: str | dict) -> dict | None:
        """
        Attempts to ensure the input is a well-formed dict with expected structure

        :param payload: The input, either a dict or JSON string
        :return: Parsed and validated dict, or None if invalid
        """
        if not isinstance(payload, dict):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                logger.error("Failed to convert tailored work experience payload to dict. Got: %s", type(payload).__name__)
                return None
        return payload

    def update_work_exp(self, updated_work_exp: dict) -> bool:
        """
        Updates resume dict's work experience section

        :param updated_work_exp: work experience that should be retrieved from LLM
        """ 
        updated_work_exp = self.parse_work_experience(updated_work_exp)
        if updated_work_exp is None:
            return False
        old_work_exp = self.resume["data"]["work_experience"]
        
        if len(old_work_exp) != len(updated_work_exp):
            logger.error("Failed to update work history", exc_info=True)
            return False
        for old_exp, updated_exp in zip(old_work_exp.values(), updated_work_exp.values()):
            if old_exp["title"] == updated_exp["title"]: 
                old_exp["responsibilities"] = updated_exp["responsibilities"]
        return True
            
    async def get_tailored_work_exp(self, job_desc: str, max_retries: int = 3, delay: float = 2.0) -> dict | None:
        """
        Makes LLM tailor resume job descriptions based on the job posting

        :param job_desc: job description from job posting
        :return: LLM response which should be in json format converted to dict
        """ 

        # only grabs work responsibilities from resume dict
        extracted_exp = {
            key: {
                "title": value["title"],
                "responsibilities": value["responsibilities"]
            }
            for key, value in self.resume["data"]["work_experience"].items()
        }

        prompt = (
            "You are a resume optimization assistant. I will give you a json containing my job title and a list of my job "
            "responsibilities along with a job posting description. Your job is to rewrite and select 5 bullet points per role "
            "that are most relevant to the job description. You are allowed to combine bullets as well. Format the rewrite in pure json, "
            "the same way as my job responsibilities. Do not include any markdown or explanations. Use double quotes. No periods. "
            "Here is my experience and the job app:\n" + json.dumps(extracted_exp) + "\n" + job_desc
        )

        client = genai.Client()

        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                logger.info(f"LLM tailoring succeeded on attempt {attempt}")
                return json.loads(response.text)
            except TimeoutException:
                logger.warning(f"Timeout on attempt {attempt}, retrying in {delay} seconds...")
            except RequestError as req_err:
                logger.error(f"Request failed: {req_err}")
                break
            except (json.JSONDecodeError, TypeError):
                logger.error("Failed to convert tailored work experience response to dict")
                break
            except Exception as e:
                logger.exception("Unexpected error occurred while tailoring resume")
                break

            await asyncio.sleep(delay)

        logger.error("All attempts to tailor resume failed")
        return None

    
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
        """
        Converts BeautifulSoup object into an html file

        :param file_name: name of html file
        """ 
        self.f_handler.write_to_html(self.parsed_template, file_name) # TODO file name needs to be changed    

    async def generate_tailored_resume(self, url: str):
        job_post_scraping = await self.scraper.scrape_job_posting(url)
        tailored = await self.get_tailored_work_exp(self.scraper.job_description)
        self.update_work_exp(tailored)
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

    