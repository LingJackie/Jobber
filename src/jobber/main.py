from job_post_scraper import JobPostScraper
from resume_tailor import ResumeTailor
from file_handler import FileHandler
from hotkey_listener import HotkeyListener
import asyncio
import keyboard




async def main():
    f_handler = FileHandler()
    jackie_resume = await f_handler.load_resume_data_async("jackie_ling_data.json")
    resume_template = await f_handler.load_resume_template_async("default_resume_template.html")
    
    rw = await ResumeTailor.set_scraper(jackie_resume, resume_template)
    await rw.generate_tailored_resume_async(r"https://www.oneforma.com/jobs/agate-photo-style-editor/")


    # stuff = await rw.generate_tailored_resume_async("https://job-boards.greenhouse.io/greenhouse/jobs/6605179?gh_jid=6605179")
    # stuff = await rw.generate_tailored_resume_async(r"https://mjhlifesciences.wd1.myworkdayjobs.com/Careers/job/Cranbury-NJ/Web-Content-Coordinator_JR102043?source=Linkedin")
    # await rw.generate_tailored_resume_async(r"https://job-boards.greenhouse.io/addepar1/jobs/7927017002")   

async def test_scraper():
    scraper = await JobPostScraper.fetch_configs()
    await scraper.scrape_job_posting_async(r"https://jobs.jobvite.com/careers/webmd/job/onYtwfw4?__jvst=Career%20Site")    
    print("Title: ", scraper.job_title)
    print("Location: ", scraper.job_location)
    # print(scraper.job_salary)
    print(scraper.job_description)
    print("Company Name: ",scraper.company_name)

async def save_new_pdf():
    f_handler = FileHandler()
    await f_handler.generate_pdf_async("2025-07-17_03-19_n-a_associate-applied-technology-developer_v1", "Jackie_Ling_Resume.pdf", "resume_wip.html")
    

# asyncio.run(main())
# asyncio.run(test_scraper())
# asyncio.run(save_new_pdf())

async def hm():
    listener = await HotkeyListener.create()
    try:
        await listener.listen()
    except KeyboardInterrupt:
        print("👋 Interrupted by user.")
        listener.stop()

asyncio.run(hm())