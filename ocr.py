import os
import base64
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = os.getenv("API_URL")
if not API_URL:
    raise ValueError("API_URL not found in .env file")
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN not found in .env file")
MODEL = os.getenv("MODEL")
if not MODEL:
    raise ValueError("MODEL not found in .env file")
OCR_PROMPT = """These images are segments of a book we are converting into structured json. Ensure that all content from 
the page is included, such as headers, subtexts, graphics (with alt text if possible), tables, and any other 
elements. You will be provided the output of the first pass of running OCR on these pages.

Requirements:
  - Output Only JSON: Return solely the JSON content without any additional explanations or comments.
  - No Delimiters: Do not use code fences or delimiters like ```markdown.
  - Complete Content: If present, do not omit any part of the page, including headers, block quotes, and subtext.
  - Accurate Content: Do not include parts that don't exist. If there is no header, footers, etc., do not include them.
  - Correct any OCR mistakes, including spelling, incorrect line breaks, or invalid characters.

Style Guide
  - Output as an array of objects. In the format of {"type":"section_type","content":"section content"}
  - Types should be header, sub_header, chapter_header, paragraph, page_division, bold, block_indent.

Example:
[
{"type":"header","content":"The Great Book Title"},
{"type":"sub_header","content":"A guide to writing great book title"},
{"type":"chapter_header","content":"1"},
{"type":"paragraph","content":"Books are comprised of words on a page..."},
{"type":"block_indent","content":"'This is a famous quote' - Some Guy"},
{"type":"paragraph","content":"Some additional words go ina paragraph..."}
]
"""
IMAGE_DIRECTORY = "out"


def process_images():

    text_files = []

    for filename in os.listdir(IMAGE_DIRECTORY):
        if not filename.endswith(".txt"):
            continue

        txt_full_path = os.path.join(IMAGE_DIRECTORY, filename)
        if not os.path.isfile(txt_full_path):
            continue

        img_full_path = os.path.join(IMAGE_DIRECTORY, filename.replace(".txt", ".png"))
        if not os.path.isfile(img_full_path):
            continue

        text_files.append(filename)

    text_files.sort()

    # Get all files in the image directory
    for filename in text_files:
        if not filename.endswith(".txt"):
            continue

        txt_full_path = os.path.join(IMAGE_DIRECTORY, filename)
        if not os.path.isfile(txt_full_path):
            continue

        img_full_path = os.path.join(IMAGE_DIRECTORY, filename.replace(".txt", ".png"))
        if not os.path.isfile(img_full_path):
            continue

        json_full_path = os.path.join(IMAGE_DIRECTORY, filename.replace(".txt", ".json"))
        if os.path.isfile(json_full_path):
            continue

        print(f"Processing {txt_full_path}")

        try:
            # Read the image file
            with open(img_full_path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode("utf-8")
            # Read the text file
            with open(txt_full_path, "r") as f:
                text_content = f.read()

            # Prepare the API request payload
            payload = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": OCR_PROMPT + "\n\n# OCR CONTENT\n\n" + text_content
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encoded_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 20000
            }

            response = requests.post(API_URL, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_TOKEN}"
            }, json=payload)

            if response.status_code == 200:
                # Process and save the response
                response_data = response.json()
                msg_content = response_data['choices'][0]['message']['content']
                parsed = list(json.loads(msg_content))

                print("DEBUG -- -- \n", json.dumps(parsed, indent=2))

                if len(parsed) == 0:
                    print(f"No sections exist in json output!")
                    raise ValueError

                # Save the markdown output
                with open(json_full_path, "w") as f:
                    f.write(json.dumps(parsed, indent=2))

                print(f"Successfully processed {filename}")
            else:
                print(f"Error in API response for {filename}: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    process_images()