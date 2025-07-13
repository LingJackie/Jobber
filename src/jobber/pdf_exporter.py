
import pdfkit
import base64
from pathlib import Path
from playwright.async_api import async_playwright

# margins_size = '0.75in'
# pdf_dpi = 300
# max_page_length = pdf_dpi * 11.5 # dpi * page length in inches
# options = {
#         'page-size': 'Letter',
#         'margin-top': margins_size,
#         'margin-right': margins_size,
#         'margin-bottom': margins_size,
#         'margin-left': margins_size,
#         'encoding': "UTF-8",
#         "dpi": pdf_dpi  # Higher DPI for better accuracy
#     }
# os.chdir(os.path.dirname(os.path.abspath(__file__))) # Manually sets the current working directory. IDK why, but its bugged and without it, the directory is wrong
# current_dir = os.getcwd()

# # wkhtmltopdf
# path_wkhtmltopdf = os.path.join(current_dir, r"wkhtmltopdf\bin\wkhtmltopdf.exe")
# config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# # html_resume = "Jackie_Ling_Resume.html"
# # pdf_resume = "Jackie_Ling_Resume.pdf"



# #     return str(self.parsed_html)

# def save_html(html_path):
#     self.parsed_html = Beautifulself.parsed_html(html_path, "html.parser")

# def convert_html_to_pdf(html_path):
#     # Load HTML content from a file or variable
#     try:
#         with open(html_path, "r", encoding="utf-8") as file:
#             html_file = file.read()
#         # Trim content to fit one page
#         # final_html = trim_pdf(html_file)
#         # Convert the final HTML to PDF
#         pdfkit.from_string(html_file, path_pdf_resume, options=options, configuration=config)
#         print("PDF successfully generated within one page!")
#     except Exception as e:
#         print("ERROR - Could not generate PDF")
#         print(e)

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()

#         # Load your local HTML file (replace with your actual file path or URL)
#         page.goto(path_html_resume)

#         # Evaluate scrollHeight of entire document
#         scroll_height = page.evaluate("document.documentElement.scrollHeight")
#         print(f"Page ScrollHeight: {scroll_height}px")

#         browser.close()




class PDFExporter:
    def __init__(self, margins_size: str = "0.75in", dpi: int = 300, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent.parent
        self.margins_size = margins_size
        self.dpi = dpi
        self.max_page_length = dpi * 11.5
        self.options = {
            'page-size': 'Letter',
            'margin-top': margins_size,
            'margin-right': margins_size,
            'margin-bottom': margins_size,
            'margin-left': margins_size,
            'encoding': "UTF-8",
            'dpi': dpi
        }
        self.config = pdfkit.configuration(wkhtmltopdf = str(self.base_dir / 'wkhtmltopdf' / 'bin' / 'wkhtmltopdf.exe'))


    def export(self, html: str, output_path: str):
        html = str(self.base_dir / 'output.html')
        output_path = str(self.base_dir / 'output.pdf')
        with open(html, "r", encoding="utf-8") as file:
            html_file = file.read()
        pdfkit.from_string(html_file, output_path, options=self.options, configuration=self.config)

    async def print_length(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Load your local HTML file (replace with your actual file path or URL)
            await page.goto(str(self.base_dir / 'output.html'))

            # Evaluate scrollHeight of entire document
            scroll_height = await page.evaluate("document.documentElement.scrollHeight")
            print(f"Page ScrollHeight: {scroll_height}px")

            await browser.close()

    async def generate_pdf(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(str(self.base_dir / 'output.html'))

            # Connect to Chrome DevTools Protocol
            client = await context.new_cdp_session(page)

            # Trigger PDF generation
            pdf_data = await client.send("Page.printToPDF", {
                "preferCSSPageSize": False,
                'marginLeft': 0,
                'marginRight': 0,
                'marginTop': 0,
                'marginBottom': 1
            })
            output_path = str(self.base_dir / 'output.pdf')
            # Save to file
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(pdf_data["data"]))


            await browser.close()

           




# [YYYY-MM-DD]_[CompanyName]_[JobTitle]_v1
