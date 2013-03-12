MHacks_Iris
===========

Fuckin da best!!!!!

Setup
===========

##### Necessary Resources:
2 webcams for the helmet.<br />
Access to Amazon AWS.<br />

##### Steps to get up and running:
1. Setup the AWS resources: 

  ```
  python aws/setup.py
  python mysql/setup.py
  ```

2. Start the OCR server and node.js webserver on EC2:

  ```
  ssh -i keypair ubuntu@ec2-instance
  ```
  (on the ec2-instance)
  ```
  git clone git://github.com/Transfinity/MHacks_Iris.git
  cd MHacks_Iris/
  nohup python aws/ocr_server.py
  cd webserver/
  nohup sudo node app.js
  ```
  
3. Run the helmet:
  ```
  python main.py
  ```


Libraries and Tools:
===========

#### For Opencv:
python-opencv<br />
opencv<br />

#### For Twitter Access:
python-twitter<br />
python-httplib2<br />
python-oauth2<br />
python-simplejson<br />

#### For OCR:
tesseract-ocr<br />
python-tesseract (see [Install instructions](http://code.google.com/p/python-tesseract/wiki/HowToInstallPythonTesseractDeb))

#### For AWS Resources access:
python-boto<br />

#### For the webapp:
node.js
twitter-bootstrap
