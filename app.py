from flask import Flask, flash, request, redirect, url_for, render_template
import boto3
import os
import base64
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/home/ubuntu/Face-Track/Uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
aws_client=boto3.client('rekognition')

@app.route('/')
def home():
	response=aws_client.list_collections()
	print(response)
	if response['CollectionIds'] == []:
		classes = "There are no classes"
		selectedClass = 'Null'
		return render_template('index.html', classes=classes, selectedClass=selectedClass)
	classes = response['CollectionIds']

	
	selectedClass = request.args.get('selectedClass', None)
	if selectedClass == None:
		selectedClass = classes[0]

	faces_response=aws_client.list_faces(CollectionId=selectedClass,MaxResults=123)
	faces_list = faces_response['Faces']
	if not faces_list:
		faces_list = 'Null'
	else:
		count = 1
		for item in faces_list:
			item['Id'] = count
			count = count + 1
	return render_template('index.html', classes=classes, selectedClass=selectedClass, faces_list=faces_list)

@app.route('/add-class', methods=['GET', 'POST'])
def add_collection():
	if request.method == "POST":
		collectionId = request.form['name']
		response=aws_client.create_collection(CollectionId=collectionId)
		return redirect(url_for('home'))
	return render_template('addclass.html')

@app.route('/class/<collectionId>/delete')
def delete_collection(collectionId):
	response=aws_client.delete_collection(CollectionId=collectionId)
	return redirect(url_for('home'))

@app.route('/<collectionId>/add-face', methods=['GET', 'POST'])
def add_face(collectionId):
	if request.method == 'POST':
		# check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			with open(file_path, "rb") as image_file:
				encoded_string = base64.b64encode(image_file.read())
				decoded_image = base64.b64decode(encoded_string)
				aws_client.index_faces(CollectionId=collectionId, Image={'Bytes': decoded_image},
					ExternalImageId=request.form['name'])
				return redirect(url_for('home', selectedClass=collectionId))
	return render_template('addface.html', className=collectionId)

@app.route('/class/<collectionId>/delete-face/<faceId>')
def delete_face(collectionId,faceId):
	faces = []
	faces.append(faceId)
	response=aws_client.delete_faces(CollectionId=collectionId, FaceIds=faces)
	return redirect(url_for('home', selectedClass=collectionId))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__=='__main__':
	app.run(debug=True,host="0.0.0.0",port=80)