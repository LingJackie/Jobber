import logging
import json
import asyncio
from google import genai
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
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
        
    def _parse_work_experience(self, payload: str | dict) -> dict | None:
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

    def _update_work_exp(self, updated_work_exp: dict) -> bool:
        """
        Updates resume dict's work experience section

        :param updated_work_exp: work experience that should be retrieved from LLM
        """ 
        updated_work_exp = self._parse_work_experience(updated_work_exp)
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
            
    async def _get_tailored_work_exp(self, job_desc: str, num_bullets: int = 4, max_retries: int = 3, delay: float = 2.0) -> dict | None:
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
            "responsibilities along with a job posting description. Your job is to rewrite and select " + str(num_bullets) + " bullet points per role. "
            "Order them by importance and relevance to the job description. "
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

    
    def _populate_resume(self):
        """
        Adds data from self.resume into a soup

        :param job_desc: job description from job posting
        :return: LLM response which should be in json format
        """ 
        section = self.parsed_template.find(id="work-experience")

        # Inject each experience as a complete block
        for exp in self.resume["data"]["work_experience"].values():# TODO Placeholder
            div = self.parsed_template.new_tag("div", **{"class": "experience"})
            table = self.parsed_template.new_tag("table")

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
            date.string = f"{exp['start']} - {exp['end']}"
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
            section.append(div)
            div.append(table)
            table.append(tbody)
            div.append(ul)

    def _write_resume_to_html(self) -> bool :
        """
        Converts BeautifulSoup object into an html file and places its own directory based on the job posting and timestamp
        """ 
        output_dir = self.f_handler.output_dir / self._get_output_dir_name() 
        output_dir.mkdir(parents=True, exist_ok=True)
        file_name = "resume_wip.html"
        return self.f_handler.save_html(self.parsed_template, str(output_dir / file_name)) 
        
    def _slugify(self, text: str) -> str:
        """
        Converts a string into a slug format (lowercase, spaces replaced with dashes)

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
    
    def _get_output_dir_name(self) -> str:
        """
        Create a new directory name based on timestamp_companyname_title
        Should look something like this: '2025-07-13_04-34_Spotlist-Inc_Software-Engineer_v1'
                                        
        """ 
        new_company_name = self._slugify(self.scraper.company_name)
        new_job_title = self._slugify(self.scraper.job_title)
        return f"{self._get_timestamp()}_{new_company_name}_{new_job_title}_v1"

    def _generate_resume_pdf_name(self) -> str:
        """
        Generates a resume file name based on the applicant's name 
        Example: 'Jackie_Ling_Resume.pdf'
        """ 
        name = self.resume['data']['contact_info']['name']
        name = name.replace(" ", "_")
       
        return f"{name}_Resume.pdf"
    
    async def generate_tailored_resume(self, url: str):
        """
        Pipeline:
            1. Scrape job posting
            2. Prompt LLM with job description + your own work experience
            3. Parse LLM response
            4. Insert LLM response into template and save as new html resume
            5. Convert html resume to pdf
        """ 
        job_post_scraping = await self.scraper.scrape_job_posting(url)
        tailored = await self._get_tailored_work_exp(self.scraper.job_description)
        self._update_work_exp(tailored)
        self._populate_resume()
        self._write_resume_to_html()
        await self.f_handler.generate_pdf(
            dir_name=self._get_output_dir_name(),
            output_name=self._generate_resume_pdf_name()
        )


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

    