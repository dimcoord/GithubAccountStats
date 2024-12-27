from flask import Flask, render_template, request, redirect
from PIL import Image, ImageDraw
from collections import Counter
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from io import BytesIO
import requests
import base64
import io
import os

app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/")

def fetchProfileInfo(username):
    # Auth is needed to get 5,000 requests per hour on Github API
    # Your personal access token
    load_dotenv()
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

    # Headers for authentication
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # exclude_dirs = "assets, public "
    # exclude_files = " .json, .xml, .yaml, .yml, .ini, .config, .md, .txt, .rst, .png, .jpg, .jpeg, .gif, .bmp, .svg, .ico, .zip, .tar, .gz, .rar, .7z, .log, .pdf, .doc, .docx, .xls, .xlsx, .gitignore, LICENSE"
    # exclude = exclude_files.replace(" ", "")

    includes = (".py", ".pyc", ".pyo", ".pyd", ".java", ".class", ".jar", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".c", ".h", ".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".cs", ".dart", ".gd", ".rb", ".rake", ".gemspec", ".php", ".php3", ".php4", ".php5", ".phtml", ".swift", ".go", ".rs", ".kt", ".kts", ".ts", ".tsx", ".html", ".htm", ".xhtml", ".css", ".sql", ".sh", ".bash", ".zsh", ".pl", ".pm", ".r", ".R", ".rdata", ".rds", ".m", ".mat", ".mdl", ".m", ".h", ".scala", ".sc", ".groovy", ".gvy", ".gy", ".asm", ".s", ".vb", ".vba", ".vbs", ".fs", ".fsx", ".fsi", ".pl", ".lisp", ".lsp", ".cl", ".scm", ".ss", ".tcl", ".as", ".cls", ".trigger", ".sol", ".ino", ".tex", ".sty", ".cls", ".sb", ".sb2", ".sb3")

    # Send the GET request
    html_source = requests.get(f"https://github.com/{username}?tab=repositories").text
    soup = BeautifulSoup(html_source, "lxml")
    profile = soup.find_all("li", class_="col-12 d-flex flex-justify-between width-full py-4 border-bottom color-border-muted public source")

    # Check the status code of the response
    if html_source:
        repo_list = []
        new_repo_list = []
        timestamps = []
        languages = []

        for i in profile:
            found_lang = i.find("span", itemprop="programmingLanguage")
            if found_lang is not None:
                languages.append(found_lang.get_text())
            print(languages)
            timestamps.append(i.find("relative-time").text)
            last_updated = i.find("relative-time").text
            if "4" == last_updated[-1]:
                new_repo_list.append(i.find("a"))
            elif "3" == last_updated[-1]:
                repo_list.append(i.find("a"))

        print("This year:")
        for html_tag in new_repo_list:
            repo_name = html_tag.get("href")
            url = f"https://api.github.com/repos{repo_name}/contents"

            def get_contents(url):
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"Error fetching {url}: {response.status_code}")
                    return []

                contents = response.json()
                return contents

            # Only counts this year's LOC
            def process_contents(contents):
                total = 0
                for item in contents:
                    if item['type'] == 'file':
                        # Only count lines in certain file types (e.g., .py, .js, .java, etc.)
                        if item['name'].endswith(includes):
                            file_url = item['download_url']
                            file_response = requests.get(f"{file_url}", headers=headers)
                            print(file_response.status_code)
                            if file_response.status_code == 200:
                                total += len(file_response.text.splitlines())
                    elif item['type'] == 'dir':
                        # Recursively process directories
                        process_contents(get_contents(item['url']))
                return total
            
            # Start processing the repository contents
            new_total = process_contents(get_contents(url))

        print('You wrote ', new_total, ' lines of code this year!')
    else:
        # If the request was not successful, print the status code
        print('Failed to retrieve data')
        print('Status code:', response.status_code)

    counter = Counter(languages)
    fav_lang = counter.most_common()[:5]

    image_url = "https://drive.usercontent.google.com/u/1/uc?id=1dS9vOVdmAe6_EVZa1foetLGcfQ2BTIYY&export=download"
    response = requests.get(image_url, headers=headers)
    img = Image.open(BytesIO(response.content))

    # Get a drawing context
    d = ImageDraw.Draw(img)

    # Draw the text on the image
    d.text((100, 50), "Github Wrapped 2024", fill="white", font_size=80)
    d.text((100, 200), f"Congrats, {username}!", fill="white", font_size=30)
    d.text((100, 250), f"You've written {new_total} lines of code this year!", fill="white", font_size=30)
    d.text((100, 350), f"Your favourite programming/scripting language is {fav_lang[0][0]}", fill="white", font_size=30)
    mult = 1
    for i in fav_lang[1:]:
        d.text((100, 400+(50*mult)), f"{i[0]}", fill="white", font_size=30)
        mult += 1

    # Save the image to a BytesIO object
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Return the image
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return img_base64

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    if request.method == "POST":
        username = request.form["username"]
        if username:
            output = fetchProfileInfo(username)
            return render_template('result.html', output=output)
    else:
        return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)