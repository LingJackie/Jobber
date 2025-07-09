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
    # stuff = await rw.generate_tailored_resume("https://job-boards.greenhouse.io/greenhouse/jobs/6605179?gh_jid=6605179")
    stuff = await rw.generate_tailored_resume(r"https://www.alticeusacareers.com/job/Bethpage-Software-Development-Engineer-I-NY-11714/1305785100/?feedId=414300&utm_source=linkedin&utm_campaign=Altice_Circa")


    # job_scraper = JobPostScraper()
    # stuff = await job_scraper.scrape_job_posting("https://www.rwjbarnabashealthcareers.org/job/application-analyst-i-information-systems-it-oceanport-nj-179-0000194751/?source=LinkedIn")
    # print(job_scraper.company_name)
    # print(job_scraper.job_title)
    # print(job_scraper.job_description)

    # tailor1 = ResumeTailor(load_resume_data("jackie_ling_data.json"))

    # stuff2 = await tailor1.tailor_job_desc(job_scraper.job_description)
    # print(stuff2)
  

asyncio.run(main())




