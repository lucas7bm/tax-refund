import flask, uuid, extract, os, requests
from flask import request, jsonify
from time import sleep
from io import BytesIO

app = flask.Flask(__name__)
app.config["DEBUG"] = True

test_filepath = "./inputs/09.pdf"
temp_folder = "./temp/"

external_api = "http://localhost:3000/refunds"

@app.route('/extract_from_pdf', methods=['GET'])
def home():
    return '<!doctype html><html><head><title>Upload your files!</title></head><body><h1>File Upload</h1><form method="POST" action="" enctype="multipart/form-data"><p><input type="file" name="files" multiple></p><p><input type="submit" value="Submit"></p></form></body></html>'

@app.route('/extract_from_pdf', methods=['POST'])
def upload():
    response = []
    estimativa = []
    for fi in request.files.getlist('files'):
        filepath = "./temp/" + uuid.uuid4().hex + ".pdf"
        fi.save(filepath)
        filename = fi.filename
        extracted_data = extract.from_pdf(filepath, filename)
        summarized_results = [{
            "company" : extracted_data['empresa'],
            "month" : extracted_data['competencia'],
            "mono" : extracted_data['MONO_NAO_DECLARADO'],
            "aliquot" : extracted_data['ALIQ'],
            "refund" : extracted_data['SALDO_A_RECUPERAR'],
        }]
        print(summarized_results)
        r = requests.post(url=external_api, json=summarized_results)
        print(r)
        estimativa.append(extracted_data)
        try:
            os.remove(filepath)
        except Exception as e:
            print(e)
    response = jsonify(estimativa)
    return response
        
app.run()