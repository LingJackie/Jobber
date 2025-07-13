from job_post_scraper import JobPostScraper
from resume_tailor import ResumeTailor
from file_handler import FileHandler
from file_handler import FileHandler
from pdf_exporter import PDFExporter
import asyncio




async def main():
    f_handler = FileHandler()
    jackie_resume = f_handler.load_resume_data("jackie_ling_data.json")
    resume_template = f_handler.load_resume_template("default_resume_template.html")
    
    # rw = ResumeTailor(jackie_resume, resume_template)
    # # stuff = await rw.generate_tailored_resume("https://job-boards.greenhouse.io/greenhouse/jobs/6605179?gh_jid=6605179")
    # stuff = await rw.generate_tailored_resume(r"https://mjhlifesciences.wd1.myworkdayjobs.com/Careers/job/Cranbury-NJ/Web-Content-Coordinator_JR102043?source=Linkedin")


    # Export using chrome
    export = PDFExporter()
    await export.generate_pdf()

    # export.export("as","sa")
    # await export.print_length()
    
async def test1():
    export = PDFExporter()
    await export.print_length()
    

asyncio.run(main())

asyncio.run(test1())


