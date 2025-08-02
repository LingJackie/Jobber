import argparse
from pathlib import Path
from datetime import datetime
from job_post_scraper import JobPostScraper
from resume_tailor import ResumeTailor
from file_handler import FileHandler
import asyncio

class JobberCLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Tailor a resume based on a job posting URL"
        )
        self._add_arguments()

    async def setup(self):
        self.f_handler = FileHandler()
        resume_data = self.f_handler.load_resume_data("jackie_ling_data.json")
        resume_template = self.f_handler.load_resume_template("default_template.html")
        self.r_tailor = ResumeTailor(resume_data, resume_template)


    def _add_arguments(self):
        self.parser.add_argument("url", help="Job post url")
        self.parser.add_argument("--output-dir", help="Output directory")
        

    async def run(self):
        args = self.parser.parse_args()
        await self.setup()
        await self.r_tailor.generate_tailored_resume_async(args.url)


        


if __name__ == "__main__":
    asyncio.run(JobberCLI().run())
    # JobberCLI().run()