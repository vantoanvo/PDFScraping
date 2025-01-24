from flask import Flask, render_template, request
import base64
import json
import os
from openai import OpenAI
from pdf2image import convert_from_path
from urllib.parse import urlparse

app = Flask(__name__)

def pdf_to_image(pdf_path):
        #Convert pdf to image
        image = convert_from_path(pdf_path, dpi=600)[0]
        image.save('converted_image.png', 'PNG')
        return 'converted_image.png'

def encode_image():
    with open('converted_image.png', "rb") as image_file:
        return "data:image/png;base64," + base64.b64encode(image_file.read()).decode("utf-8")

def process_response(response):
    content = response.choices[0].message.content
    json_string = content.replace("```json\n", "").replace("```", "").strip()
    try:
        json_data = json.loads(json_string)
        print(json_data)
        employer_name = json_data['employer']['name']
        employer_address = json_data['employer']['address']
        employer_id = json_data['employer']['id']
        
        employee_name = json_data['employee']['name']
        employee_address = json_data['employee']['address']
        employee_ssn = json_data['employee']['ssn']
        
        gross_pay = json_data['employee']['grosspay']
        box12 = json_data['employee']['box12']
        if box12 == "":
            box12 = "None"
        return {
            "employer_name": employer_name,
            "employer_address": employer_address,
            "employer_fed_id": employer_id,
            "employee_name": employee_name,
            "employee_address": employee_address,
            "employee_ssn": employee_ssn,
            "gross_pay": gross_pay,
            "box12": box12
        }
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)

def extract_text_from_image():
    # Convert image to base64
    base64_image = encode_image()
    client = OpenAI(api_key="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")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "return only Json data for employer {name, address, id}, employee {name, address, ssn, grosspay, box12}, the keys are lowercase",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"{base64_image}"}
                    },
                ],
            }
        ],
        max_tokens = 200
    )
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    scraped_info = None  # Initialize scraped_info to None
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return render_template('index.html', error="No file part")
        
        file = request.files['pdf_file']
        if file.filename == '':
            return render_template('index.html', error="No selected file")
        
        # Save uploaded file
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)

        # Process the file
        image_path = pdf_to_image(file_path)
        response = extract_text_from_image()
        scraped_info = process_response(response)

    return render_template('index.html', data=scraped_info)
if  __name__ == "__main__":
    app.run(debug=True)
    #server: 127.0.0.1:5000