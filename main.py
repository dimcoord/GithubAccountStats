from PIL import Image, ImageDraw
from collections import Counter
from io import BytesIO
from bs4 import BeautifulSoup
import requests
import json

exclude_dirs = "assets, public "
exclude_files = " .json, .xml, .yaml, .yml, .ini, .config, .md, .txt, .rst, .png, .jpg, .jpeg, .gif, .bmp, .svg, .ico, .zip, .tar, .gz, .rar, .7z, .log, .pdf, .doc, .docx, .xls, .xlsx, .gitignore, LICENSE"
exclude = exclude_files.replace(" ", "")
print(exclude)

# Define the URL you want to send the GET request to
username = input("Input username Github: ") or " "

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
        timestamps.append(i.find("relative-time").text)
        last_updated = i.find("relative-time").text
        if "4" == last_updated[-1]:
            new_repo_list.append(i.find("a"))
        elif "3" == last_updated[-1]:
            repo_list.append(i.find("a"))

    total = 0
    new_total = 0

    print("This year:")
    for html_tag in new_repo_list:
        repo_name = html_tag.get("href")
        response = requests.get(f"https://api.codetabs.com/v1/loc?github={repo_name[1:]}&ignored={exclude}")
        data = response.json()

        # Check if the response is a list
        if isinstance(data, list):
            languages.extend([item['language'] for item in data[:-1]])
            lines_of_code = data[-1]['linesOfCode']
            new_total += lines_of_code
            print(f"LOC of {repo_name}: {lines_of_code}")
        else:
            print(f"Unexpected response format for repository {repo_name}: {data}")

    print("Last year:")
    for html_tag in repo_list:
        repo_name = html_tag.get("href")
        response = requests.get(f"https://api.codetabs.com/v1/loc?github={repo_name[1:]}&ignored={exclude}")
        data = response.json()

        # Check if the response is a list
        if isinstance(data, list):
            languages.extend([item['language'] for item in data[:-1]])
            lines_of_code = data[-1]['linesOfCode']
            total += lines_of_code
            print(f"LOC of {repo_name}: {lines_of_code}")
        else:
            print(f"Unexpected response format for repository {repo_name}: {data}")

    print('You wrote ', new_total, ' lines of code this year!')
    print('And also ', total, ' lines of code last year')
else:
    # If the request was not successful, print the status code
    print('Failed to retrieve data')
    print('Status code:', response.status_code)

counter = Counter(languages)
fav_lang = counter.most_common()[:5]

def create_image_with_text(output_filename="output.png"):

    image_url = "https://drive.usercontent.google.com/u/1/uc?id=1dS9vOVdmAe6_EVZa1foetLGcfQ2BTIYY&export=download"
    response = requests.get(image_url)
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

    # Save the image
    display(img)

# Example usage
create_image_with_text("hello_world.png")