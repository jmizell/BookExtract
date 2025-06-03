import os
import base64
import requests
import json

# Configuration
API_URL = "https://ollama.rudd3r.com/api/generate"
MODEL = "llama3.2-vision:11b-instruct-q8_0"
PROMPT = """Convert the provided image into Markdown format. Ensure that all content from the page is included, 
such as headers, footers, subtexts, images (with alt text if possible), tables, and any other elements.

Requirements:

  - Output Only Markdown: Return solely the Markdown content without any additional explanations or comments.
  - No Delimiters: Do not use code fences or delimiters like ```markdown.
  - Complete Content: If present, do not omit any part of the page, including headers, footers, and subtext.
  - Accurate Content: Do not include parts that don't exist. If there is no header, footers, etc, do not include thne. 
"""

IMAGE_DIRECTORY = "images"


def process_images():
    # Get all files in the image directory
    for filename in os.listdir(IMAGE_DIRECTORY):
        full_path = os.path.join(IMAGE_DIRECTORY, filename)
        if not os.path.isfile(full_path):
            continue

        try:
            # Read the image file
            with open(full_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

            # Prepare the API payload
            payload = {
                "model": MODEL,
                "prompt": PROMPT,
                "stream": False,
                "images": [encoded_image]
            }

            # Make the API request
            response = requests.post(
                API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            # Check if the response was successful
            if response.status_code == 200:
                try:
                    # Extract the response data
                    response_data = response.json()
                    print(f"Successfully processed {filename}")
                    # print(json.dumps(response_data, sort_keys=True, indent=2))
                    print(response_data["response"])
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON response for {filename}")
            else:
                print(f"API request failed for {filename}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    process_images()