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
    # stuff = await rw.generate_tailored_resume(r"https://mjhlifesciences.wd1.myworkdayjobs.com/Careers/job/Cranbury-NJ/Web-Content-Coordinator_JR102043?source=Linkedin")
    # await rw.generate_tailored_resume(r"https://job-boards.greenhouse.io/addepar1/jobs/7927017002")
    await rw.generate_tailored_resume(r"https://www.oneforma.com/jobs/agate-photo-style-editor/")


async def test1():
    scraper = JobPostScraper()
    await scraper.scrape_job_posting(r"https://www.oneforma.com/jobs/agate-photo-style-editor/")    
    print(scraper.job_title)
    print(scraper.job_location)
    # print(scraper.job_salary)
    print(scraper.job_description)
    print("company name ",scraper.company_name)
async def save_new_pdf():
    f_handler = FileHandler()
    
    await f_handler.generate_pdf("2025-07-15_02-51_n-a_agate-photo-style-editor_v1", "Jackie_Ling_Resume.pdf", "resume_wip.html")
    

# asyncio.run(main())
# asyncio.run(test1())
asyncio.run(save_new_pdf())


