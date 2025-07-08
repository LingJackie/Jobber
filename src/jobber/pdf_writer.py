import io
import re
import pdfkit
import subprocess
import PyPDF2
from bs4 import Beautifulself.parsed_html
import os
from playwright.sync_api import sync_playwright

margins_size = '0.75in'
pdf_dpi = 108
max_page_length = pdf_dpi * 11.5 # dpi * page length in inches
options = {
        'page-size': 'Letter',
        'margin-top': margins_size,
        'margin-right': margins_size,
        'margin-bottom': margins_size,
        'margin-left': margins_size,
        'encoding': "UTF-8",
        "dpi": pdf_dpi  # Higher DPI for better accuracy
    }
os.chdir(os.path.dirname(os.path.abspath(__file__))) # Manually sets the current working directory. IDK why, but its bugged and without it, the directory is wrong
current_dir = os.getcwd()

# wkhtmltopdf
path_wkhtmltopdf = os.path.join(current_dir, r"wkhtmltopdf\bin\wkhtmltopdf.exe")
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# html_resume = "Jackie_Ling_Resume.html"
# pdf_resume = "Jackie_Ling_Resume.pdf"


# TODO needs a way to check if file name is valid
class PDFWriter:
    def __init__(self, resume_template: str):
        """
        :param resume_template: html resume template file
        """ 
        self.resume_template = resume_template
        self.resume_final = resume_template[:resume_template.find(".")] + ".pdf"

        self.resume_template_path = os.path.join(current_dir, "resources", resume_template)
        self.resume_final_path = os.path.join(current_dir, "resources", self.resume_final)

# def get_pdf_page_count(pdf_path):
#     try:
#         with open(pdf_path, 'rb') as file:
#             reader = PyPDF2.PdfReader(file)
#             return len(reader.pages)
#     except:
#         print("ERROR - Could not get page count of: ", pdf_path)
#         return -1

# # Checks if HTML resume fits in a single page or not 
# def check_pdf_fits(html_path):
#     # Generates a temporary PDF so page number can be checked 
#     temp_pdf = "temp_output.pdf"
#     try:
#         pdfkit.from_string(html_path, temp_pdf, options=options)
#         return True if get_pdf_page_count(temp_pdf) == 1 else False
#     except:
#         print("ERROR - Unable to check pdf's fit")
#         return False
    
# # TODO: NEEDS TO REMOVE BASED OFF KEYWORDS
# # Trims pdf to ensure its is one page long
# def trim_pdf(html_path):
#     """ Removes bullet points iteratively until the content fits on one page """
#     self.parsed_html = Beautifulself.parsed_html(html_path, "html.parser")
#     bullet_points = self.parsed_html.find_all("li")
#     while not check_pdf_fits(str(self.parsed_html)) and bullet_points:
#         bullet_points[-1].extract()  # Remove the last bullet point
#         bullet_points = self.parsed_html.find_all("li")  # Refresh list after modification

    
#     return str(self.parsed_html)

def write_to_html(html_path):
    self.parsed_html = Beautifulself.parsed_html(html_path, "html.parser")

def convert_html_to_pdf(html_path):
    # Load HTML content from a file or variable
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            html_file = file.read()
        # Trim content to fit one page
        # final_html = trim_pdf(html_file)
        # Convert the final HTML to PDF
        pdfkit.from_string(html_file, path_pdf_resume, options=options, configuration=config)
        print("PDF successfully generated within one page!")
    except Exception as e:
        print("ERROR - Could not generate PDF")
        print(e)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Load your local HTML file (replace with your actual file path or URL)
        page.goto(path_html_resume)

        # Evaluate scrollHeight of entire document
        scroll_height = page.evaluate("document.documentElement.scrollHeight")
        print(f"Page ScrollHeight: {scroll_height}px")

        browser.close()







convert_html_to_pdf(path_html_resume)



'''
Pipeline:
1. Convert a pdf to html
2. Copy job app to clipboard
3. read clipboard contents
4. grab keywords and stuff from app
5. only add job description bullts that contain keywords
6. update skills section accordingly
7. convert back to pdf
'''