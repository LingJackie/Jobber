from bs4 import BeautifulSoup
from file_handler import FileHandler
import json
#USE tqdm for progress bar
# Takes the resume dict and replace the work responsibilities with the llm response then write to html





class ResumeWriter():
    # Your structured experience data
    experience_data = {
        "experience_1":{
                    "title": "Junior Software Engineer",
                    "company": "Genspark",
                    "start": "Apr 2022",
                    "end": "Jan 2023",
                    "location": "Middletown, NJ",
                    "responsibilities": [
                    "Built web apps for a Large Telecomunications client",
                    "Worked with people across time zones, using tools like MS Teams, Bitbucket, and Jira",
                    "Used Bitbucket to manage code version control",
                    "Tech stack was Angular and Node.js for some projects and React and Springboot for others",
                    "Style the front end with Angular",
                    "Worked on RESTful APIs in the backend with Node.js",
                    "Wrote SQL queries to grab data from relational databases",
                    "Used npm to manage dependencies",
                    "Worked with senior developers to troubleshoot technical issues",
                    "Wrote automated unit and integration tests",
                    "Optimized dashboard table components performances, improving load times by an estimated 15%",
                    "Worked in an Agile team that tracked project tasks and bugs using Jira",
                    "Worked on a job tracking webapp for client's service technicians",
                    "Worked on a employee management webapp. The dashboard tracked the technicians",
                    "Wrote and improved internal documentation including onboading docs, reducing onboarding time by approximately 20%"
                    ]
                }
        # Add more experiences like "experience_3", "experience_4", etc.
    }

    llm_response = '{"experience_1": {"title": "Junior Software Engineer", "responsibilities": ["Developed and maintained robust RESTful APIs with Node.js, including writing SQL queries for efficient data management", "Implemented comprehensive software engineering practices, including automated unit and integration testing and version control with Bitbucket", "Optimized dashboard component performance, leading to an estimated 15% improvement in load times, showcasing a focus on efficiency", "Collaborated effectively within cross-functional Agile teams using Jira and MS Teams for project tracking and issue resolution", "Authored and improved internal documentation, including onboarding guides, which reduced onboarding time by approximately 20%"]}, "experience_2": {"title": "Software Engineer Intern", "responsibilities": ["Gained practical experience deploying applications on AWS, utilizing EC2 for hosting and S3 for efficient data storage", "Developed backend functionalities using Django and PostgreSQL, including designing, testing, and documenting RESTful API endpoints with Postman", "Integrated third-party APIs such as Stripe for secure payment processing, emphasizing data security and best practices", "Contributed to an Agile development team, actively participating in sprint ' \
    'planning and daily stand-ups, and managing codebase changes using Git", "Supported knowledge transfer by contributing to technical documentation and effectively communicating project progress to stakeholders"]}}'
    python_dict = json.loads(llm_response)
    experience_data["experience_1"]["job_description"]= python_dict["experience_1"]["responsibilities"]

    def __init__(self, template: str):
        """
        :param template: html resume template located in the 'templates' directory
        :return: domain and extension (Example: "myworkdayjobs.com")
        """ 
        self.f_handler = FileHandler()
        self.parsed_html = self.f_handler.load_resume_template(template)

    def populate_resume(self):
                
        
        section = self.parsed_html.find(id="work-experience")

        # Inject each experience as a complete block
        for exp in self.__class__.experience_data.values():# TODO Placeholder
            table = self.parsed_html.new_tag("table", **{"class": "experience"})

            tbody = self.parsed_html.new_tag("tbody")
            tr_left = self.parsed_html.new_tag("tr")
            tr_right = self.parsed_html.new_tag("tr")
            tbody.append(tr_left)
            tbody.append(tr_right)

            title = self.parsed_html.new_tag("td", **{"class": "title"})
            title.string = exp["title"]
            date = self.parsed_html.new_tag("td", **{"class": "date"})
            date.string = f"{exp['start']} – {exp['end']}"
            tr_left.append(title)
            tr_left.append(date)

            company = self.parsed_html.new_tag("td", **{"class": "company"})
            company.string = exp["company"]
            location = self.parsed_html.new_tag("td", **{"class": "location"})
            location.string = exp["location"]
            tr_right.append(company)
            tr_right.append(location)


            # Bullet points
            ul = self.parsed_html.new_tag("ul", **{"class": "bullets"})
            for bullet in exp["responsibilities"]:
                li = self.parsed_html.new_tag("li")
                li.string = bullet
                ul.append(li)

            # Assemble and inject
            
            section.append(table)
            table.append(tbody)
            section.append(ul)

        self.f_handler.write_html_resume(self.parsed_html,"output.html") # TODO file name needs to be changed









