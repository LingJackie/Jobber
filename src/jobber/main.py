from job_post_scraper import JobPostScraper
from resume_tailor import ResumeTailor
from file_handler import FileHandler
from file_handler import FileHandler
import asyncio




async def main():
    f_handler = FileHandler()
    jackie_resume = f_handler.load_resume_data("jackie_ling_data.json")
    resume_template = f_handler.load_resume_template("default_resume_template.html")
    
    rw = ResumeTailor(jackie_resume, resume_template)
    rw.generate_tailored_resume()

    # job_scraper = JobPostScraper()
    # stuff = await job_scraper.scrape_job_posting("https://job-boards.greenhouse.io/greenhouse/jobs/6605179?gh_jid=6605179")
    # print(job_scraper.company_name)
    

    # tailor1 = ResumeTailor(load_resume_data("jackie_ling_data.json"))

    # stuff2 = await tailor1.tailor_job_desc(job_scraper.job_description)
    # print(stuff2)
  

asyncio.run(main())




