from flask import *
import numpy as np
import os
from functools import wraps
import webbrowser
import ctypes

from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image
from flask_mysqldb import MySQL
from tqdm import tqdm
import hashlib
import controller as ct
import cv2
import time

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.lib.utils import ImageReader
from PIL import Image

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch

app=Flask(__name__, template_folder='templates', static_folder='static')
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='root'
app.config['MYSQL_DB']='ses'
app.config['MYSQL_CURSORCLASS']='DictCursor'
mysql=MySQL(app)     

@app.route('/')
def index():
    return render_template('index.html',url=url)

@app.route('/login',methods=['POST','GET'])
def login():
    status=True
    if request.method=='POST':
        email=request.form["email"]
        pwd=request.form["upass"]
        cur=mysql.connection.cursor()
        cur.execute("select * from admin where email=%s and password=%s",(email,ct.md5(pwd)))
        data=cur.fetchone()
        if data:
            session['logged_in']=True
            session['username']=data["username"]
            flash('Login Successfully','success')
            return redirect('admin_home')
        else:
            cur.execute("select * from user where email=%s and password=%s",(email,ct.md5(pwd)))
            data=cur.fetchone()
            if data:
                session['logged_in']=True
                session['username']=data["username"]
                flash('Login Successfully','success')
                return redirect('user_home')
            else:
                flash('Invalid Login. Try Again','danger')
                return redirect('login')
        flash('Invalid Login. Try Again','danger')
    return render_template("login.html",url = url)

def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, Please Login','danger')
			return redirect(url_for('login'))
	return wrap
global output_file
@app.route('/train', methods=['GET', 'POST'])
@is_logged_in
def train():
    global output_file
    return render_template('train.html',url=url,data = session['username'])

@app.route('/get_dataset', methods=['GET', 'POST'])
@is_logged_in
def get_dataset():
    if (os.listdir('Dataset')):
        count = 0
        for root_dir, cur_dir, files in os.walk(r'Dataset'):
            count += len(files)
        time.sleep(3)
        return str(count) + " images found"
    else:
        return "No dataset Found in the path specified. Copy the files to path and refresh and try again"
@app.route('/start_training', methods=['GET', 'POST'])
@is_logged_in
def start_training():
    ct.train()
    time.sleep(10)
    return "Already Trained"

@app.route('/save_model', methods=['GET', 'POST'])
@is_logged_in
def save_model():
    if(ct.save_model()):
        return "Model Saved Successfully"
    else:
        return "Failed to save model"
@app.route('/save_memo', methods=['GET', 'POST'])
@is_logged_in
def save_memo():
    time.sleep(2)
    return "Memo Saved Successfully"
@app.route('/show_accuracy', methods=['GET', 'POST'])
@is_logged_in
def show_accuracy():
    time.sleep(2)
    return send_file('Plots/accuracy.png', mimetype='image/jpg')

@app.route('/show_loss', methods=['GET', 'POST'])
@is_logged_in
def show_loss():
    time.sleep(2)
    return send_file('Plots/loss.png', mimetype='image/png')
@app.route('/predict', methods=['GET', 'POST'])
@is_logged_in
def predict():
    global output_file
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']
        file_path = os.path.join('static','input_images',secure_filename(f.filename))
        f.save(file_path)
        output_file = file_path
    return render_template('demo.html',url=url,filename = file_path)



#Registration  
@app.route('/reg',methods=['POST','GET'])
def reg():
    status=False
    if request.method=='POST':
        name=request.form["uname"]
        print(name)
        email=request.form["email"]
        print(email)
        pwd=request.form["upass"]
        print(pwd)
        cur=mysql.connection.cursor()
        cur.execute("insert into user(username,password,email) values(%s,%s,%s)",(name,ct.md5(pwd),email))
        mysql.connection.commit()
        cur.close()
        log = 'Registration Successfully. Login Now...'
        flash('Registration Successfully. Login Now...','success')
        return redirect('login')
    return render_template("register.html",url = url)


@app.route('/get_result', methods=['GET'])
def get_image():
    global output_file
    output_text = ct.predict(output_file)
    # Replace 'path_to_image' with the actual path to your image file
    return jsonify(output_text)
  


#Home page
@app.route("/admin_home",methods=['POST','GET'])
@is_logged_in
def admin_home():
    global url
    return render_template('admin_home.html',data = session['username'],url = url)

#Home page
@app.route("/user_home",methods=['POST','GET'])
@is_logged_in
def user_home():
    global url
    return render_template('user_home.html',data = session['username'],url = url)


@app.route("/logout")
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('index'))
def draw_wrapped_text(c, text, x, y, max_width, line_height, page_height):
    """
    Draws wrapped text and handles page breaks automatically
    """
    from reportlab.lib.utils import simpleSplit

    lines = simpleSplit(text, "Helvetica", 11, max_width)
    for line in lines:
        if y < 60:
            c.showPage()
            y = page_height - 50
            c.setFont("Helvetica", 11)
        c.drawString(x, y, line)
        y -= line_height
    return y

def generate_ses_pdf(report_data, image_path, username):
    pdf_path = "static/reports/SES_Report.pdf"
    os.makedirs("static/reports", exist_ok=True)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    y = height - 40

    # ---- Title ----
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, y, "Socio Economic Status Detection Report")
    y -= 30

    # ---- Meta Info ----
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Generated By : {username}")
    y -= 15
    c.drawString(50, y, f"Date : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    y -= 25

    # ---- Uploaded Image ----
    if os.path.exists(image_path):
        img = ImageReader(image_path)
        img_width = 250
        img_height = 200

        if y - img_height < 80:
            c.showPage()
            y = height - 50

        c.drawImage(
            img,
            50,
            y - img_height,
            width=img_width,
            height=img_height,
            preserveAspectRatio=True
        )
        y -= img_height + 20

    # ---- SES Category ----
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Predicted SES Category:")
    y -= 20

    c.setFont("Helvetica", 12)
    c.drawString(70, y, report_data["title"])
    y -= 30

    # ---- SES Indicators ----
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Socio Economic Indicators")
    y -= 20

    c.setFont("Helvetica", 11)

    for key, value in report_data.items():
        if key == "title" or key == "policies":
            continue

        text = f"{key.replace('_',' ')} : {value}"
        y = draw_wrapped_text(c, text, 70, y, width - 120, 16, height)
        y -= 5

    # ==============================
    # POLICY SUGGESTIONS (NEW PAGE)
    # ==============================
    if "policies" in report_data:
        c.showPage()
        y = height - 50

        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, y, "Policy Recommendations")
        y -= 40

        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"For SES Category: {report_data['title']}")
        y -= 30

        for idx, policy in enumerate(report_data["policies"], start=1):
            policy_text = f"{idx}. {policy}"
            y = draw_wrapped_text(c, policy_text, 60, y, width - 120, 18, height)
            y -= 10

    # ---- Footer ----
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, 30, "SES Detection System | Generated Report")

    c.save()
    return pdf_path


@app.route('/download_report')
@is_logged_in
def download_report():
    global output_file

    report_data = ct.predict(output_file)

    image_path = os.path.abspath(output_file)

    print("PDF IMAGE PATH:", image_path)  # DEBUG

    pdf_path = generate_ses_pdf(
        report_data,
        image_path,
        session['username']
    )

    return send_file(pdf_path, as_attachment=True)


if __name__ == '__main__':
    global url
    app.secret_key='secret123'
    myIP = ct.get_ip_address_of_host()
    url = 'http://' + myIP + ':5002'
    app.run(debug=False, host='0.0.0.0',port = 5002)

