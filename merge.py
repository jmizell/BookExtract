import os
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
PROMPT="""
These are two segments of text from an OCR task. The first segment is from the end of one page. The last segment is
from the beginning of the following page. Sometimes during OCR content is split between one page, and the next. We
need to identify when this happens, and join the content is necessary.

To join the segments write out a single segment with the combine content. To leave the segments as they are, just 
write them out as they are

Examples:

## Example Of Split Content That Needs To Be Joined
First and second page segments
```
[
{"type":"paragraph","content":"Books are comprised of words on a page"},
{"type":"paragraph","content":"that make up long sentences of text."},
]
```
To join, output this
[
{"type":"paragraph","content":"Books are comprised of words on a page that make up long sentences of text."}
]

## Example Of Segments that Should Not Be Joined
First and second page segments
```
[
{"type":"paragraph","content":"Books are comprised of words on a page that make up long sentences of text."},
{"type":"paragraph","content":"In this second paragraph, I shall refute the statement from the first."},
]
```
To leave as is, output this
```
[
{"type":"paragraph","content":"Books are comprised of words on a page that make up long sentences of text."},
{"type":"paragraph","content":"In this second paragraph, I shall refute the statement from the first."},
]
```

"""
IMAGE_DIRECTORY = "out"


def process_images():

    sections = []
    json_files = []

    for filename in os.listdir(IMAGE_DIRECTORY):
        if not filename.endswith(".json"):
            continue
        json_files.append(filename)

    json_files.sort()

    # Get all files in the image directory
    for filename in json_files:
        json_full_path = os.path.join(IMAGE_DIRECTORY, filename)
        if not os.path.isfile(json_full_path):
            continue

        print(f"Processing {json_full_path}")

        try:
            # Read the text file
            with open(json_full_path, "r") as f:
                section = json.loads(f.read())

            if len(section) == 0:
                print(f"No sections exist in json file!")
                raise ValueError

            if len(sections) == 0:
                sections = section
                continue

            # Prepare the API request payload
            payload = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": PROMPT + "\n\n# SEGMENTS FROM FIRST AND NEXT PAGE\n\n" + json.dumps([sections[len(sections)-1],section[0]])
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

                if len(parsed) == 1:
                    print(f"Merging sections")
                    sections[len(sections)-1] = parsed[0]
                    section = section[1:]
                elif len(parsed) == 2:
                    print(f"No section merge will be done")
                else:
                    print(f"Invalid response from model, {response.text}")
                    raise ValueError

                sections = sections + section
                print(f"Successfully processed {filename}")
            else:
                print(f"Error in API response for {filename}: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")


    sections_full_path = os.path.join(IMAGE_DIRECTORY, "book.json")
    with open(sections_full_path, "w") as f:
        f.write(json.dumps(sections, indent=2))
    print(json.dumps(sections, indent=2))


if __name__ == "__main__":
    process_images()