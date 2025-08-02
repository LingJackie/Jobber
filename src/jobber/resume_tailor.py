import logging
import json
import asyncio
from google import genai
from bs4 import BeautifulSoup
from datetime import datetime
from job_post_scraper import JobPostScraper
from file_handler import FileHandler
from httpx import TimeoutException, RequestError
import re
import validators


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO make use of gemini cache so I dont have to keep sending the resume
# TODO Fix bug where it would write multiple times to the same file so there would be duplicate entries
class ResumeTailor:
    """
    ResumeTailor is responsible for tailoring a resume to a specific job posting by leveraging an LLM to rewrite work experience and skills,
    By taking in a resume template, it generates output files such as an HTML and PDF.
    """

    def __init__(self, resume: dict, parsed_template: BeautifulSoup):
        """
        :param resume: dict containing resume data
        :param parsed_template: parsed resume template html
        """ 
        self.resume = resume
        self.parsed_template = parsed_template
        self.f_handler = FileHandler()
        self.most_recent_output_dir = None
        self.resume_pdf_file_name = self._generate_resume_pdf_name()


    @classmethod
    async def set_scraper(cls, resume: dict, parsed_template: BeautifulSoup):
        """
        Sets up the ResumeTailor instance with a JobPostScraper instance
        RUN this method to initialize the ResumeTailor with the necessary scraper configurations
        """
        instance = cls(resume, parsed_template)
        instance.scraper = await JobPostScraper.fetch_configs()
        return instance
        
        
    def _parse_llm_json_response(self, payload: str | dict) -> dict | None:
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

    def _update_work_exp(self, new_data: dict) -> bool:
        """
        Updates the work experience section of the resume dict with new data

        :param new_data: work experience and skills that should be retrieved from LLM
        """ 
        new_data = self._parse_llm_json_response(new_data)
        if new_data is None or "work_experience" not in new_data or not isinstance(new_data["work_experience"], dict):
            logger.error("Key 'work_experience' missing or invalid in LLM response")
            return False
        
        old_work_exp = self.resume["data"]["work_experience"]
        updated_work_exp = new_data["work_experience"]
        
        if len(old_work_exp) != len(updated_work_exp):
            logger.warning("Work experience count mismatch between old and updated data")
        for key in old_work_exp:
            if key in updated_work_exp and old_work_exp[key]["title"] == updated_work_exp[key]["title"]:
                old_work_exp[key]["responsibilities"] = updated_work_exp[key]["responsibilities"]
        # Safely update skills if present
        skills = new_data.get("skills", {})
        self.resume["data"]["skills"]["softwares"] = skills.get("softwares", [])
        self.resume["data"]["skills"]["coding_languages"] = skills.get("coding_languages", [])
        return True
    
    async def _get_tailored_work_exp_async(self, job_desc: str, num_bullets: int = 12, max_retries: int = 3, delay: float = 2.0) -> dict | None:
        """
        Makes LLM tailor resume job descriptions based on the job posting

        :param job_desc: job description from job posting
        :return: LLM response which should be in json format converted to dict
        """ 
        num_skills = 5
        extracted_exp = {
            "work_experience": {
                key: {
                    "title": value["title"],
                    "responsibilities": value["responsibilities"]
                }
                for key, value in self.resume["data"]["work_experience"].items()
            },
            "skills": {
                "coding_languages": self.resume["data"]["skills"]["coding_languages"],
                "softwares": self.resume["data"]["skills"]["softwares"]
            }
        }
        prompt = (
            "You will receive a JSON payload containing my work experience, skills, and a job posting description. "
            "Your task is to generate a revised version of my experience that is tailored to the job posting. "
            "Select and rewrite a total of" + str(num_bullets) + " bullet points across my roles that are most relevant to the job description. "
            "Each role should have at least 2 bullet point. "
            "You may combine multiple bullets if doing so improves clarity or relevance. "
            "If my work experience is from a different domain than the posting, try to emphasize transferable skills, or technical proficiencies."
            "Select at least " + str(num_skills) + "of the most relevant skills from the skills section and incorporate them appropriately. "
            "Format the rewrite in pure json, the same schema as the inputs. "
            "Do not include any markdown or explanations. Use double quotes. No periods. "
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

    
    def _update_resume_work_exp(self) -> bool:
        """
        Takes the work_experience section of self.resume and updates the work experience section of the parsed template soup object

        :return: True if the work experience section was updated successfully, False otherwise
        """
        section = self.parsed_template.find(id="work-experience")
        if section is None:
            logger.error("Could not find 'work-experience' section in the template.")
            return False

        try:
            # for element in section.find_all(recursive=False):
            #     if element.name != "h3" or element.name != "h2":  # Keep the section header
            #         element.decompose()

            # Inject each experience as a complete block
            for exp in self.resume["data"]["work_experience"].values():
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
                ul = self.parsed_template.new_tag("ul", **{"class": "exp-bullets"})
                for bullet in exp["responsibilities"]:
                    li = self.parsed_template.new_tag("li")
                    li.string = bullet
                    ul.append(li)

                # Assemble and inject
                section.append(div)
                div.append(table)
                table.append(tbody)
                div.append(ul)
            return True
        except Exception as e:
            logger.exception("Error occurred while updating work experience section: %s", e)
            return False
    
    def _update_resume_skills(self) -> bool:
        """
        Takes the skills section of self.resume and updates the skills section of the parsed template soup object

        :return: True if the skill section was updated successfully, False otherwise
        """
        section = self.parsed_template.find(id="technical_skills")
        if section is None:
            logger.error("Could not find 'technical_skills' section in the template.")
            return False
        try:
            # for element in section.find_all(recursive=False):
            #     if element.name != "h3" or element.name != "h2":  # Keep the section header
            #         element.decompose()

            table = self.parsed_template.new_tag("table")
            tbody = self.parsed_template.new_tag("tbody")
            section.append(table)
            table.append(tbody)
            for skill_type, skills in self.resume["data"]["skills"].items():
                if skill_type == "coding_languages" or skill_type == "softwares":
                    tr = self.parsed_template.new_tag("tr")
                    td1 = self.parsed_template.new_tag("td", **{"class": "skill-type"})
                    td1.string = skill_type.replace("_", " ").title() + ":"

                    td2 = self.parsed_template.new_tag("td")
                    td2.string = ", ".join(skills) if skills else "None"

                    tr.append(td1)
                    tr.append(td2)
                    tbody.append(tr)
            return True
        except Exception as e:
            logger.exception("Error occurred while updating skills section: %s", e)
            return False
               

    def _generate_resume_pdf_name(self) -> str:
        """
        Generates a sanitized resume file name based on the applicant's name.
        Example: 'Jackie_Ling_Resume.pdf'
        """

        name = self.resume['data']['contact_info'].get('name', '').strip()
        if not name or name.lower() == "n-a":
            name = "Applicant"
        else:
            # Capitalize first letter of each word
            name = " ".join(word.capitalize() for word in name.split())
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        name = self.f_handler._sanitize_file_and_directory_name(name)
        return f"{name}_Resume.pdf"
    
    async def generate_tailored_resume_async(self, url: str) -> bool:
        """
        Pipeline:
            1. Scrape job posting
            2. Prompt LLM with job description + your own work experience
            3. Parse LLM response
            4. Insert LLM response into template and save as new html resume
            5. Convert html resume to pdf
        """ 
        if not (await self.scraper.scrape_job_posting_async(url)):
            logger.error("Failed to scrape job posting from URL: %s", url)
            return False
        tailored = await self._get_tailored_work_exp_async(self.scraper.job_description)
        if not self._update_work_exp(tailored):
            logger.error("Failed to update work experience with tailored data")
            return False
        if not self._update_resume_work_exp():
            logger.error("Failed to update work experience section in the template")
            return False
        if not self._update_resume_skills():
            logger.error("Failed to update skills section in the template")
            return False
        self.most_recent_output_dir = self.f_handler.get_output_dir_name() # Keeps track of the most recent output directory if we need to edit and re-save the pdf
        if not await self.f_handler.write_resume_to_html_async(self.parsed_template, self.most_recent_output_dir):
            logger.error("Failed to write resume to HTML")
            return False
        await self.f_handler.generate_pdf_async(
            dir_name=self.most_recent_output_dir,
            output_name=self.resume_pdf_file_name
        )
        return True
    
    async def alternative_generate_tailored_resume_async(self, job_description: str) -> bool:
        """
        Similar to generate_tailored_resume_async, but takes the job description as a parameter instead of scraping it from the URL
        This is used if the scraper is unable to scrape the job posting
        """ 
        tailored = await self._get_tailored_work_exp_async(job_description)
        if not self._update_work_exp(tailored):
            logger.error("Failed to update work experience with tailored data")
            return False
        if not self._update_resume_work_exp():
            logger.error("Failed to update work experience section in the template")
            return False
        if not self._update_resume_skills():
            logger.error("Failed to update skills section in the template")
            return False
        self.most_recent_output_dir = self.f_handler.get_output_dir_name() # Keeps track of the most recent output directory if we need to edit and re-save the pdf
        if not await self.f_handler.write_resume_to_html_async(self.parsed_template, self.most_recent_output_dir):
            logger.error("Failed to write resume to HTML")
            return False
        await self.f_handler.generate_pdf_async(
            dir_name=self.most_recent_output_dir,
            output_name=self.resume_pdf_file_name
        )
        return True

