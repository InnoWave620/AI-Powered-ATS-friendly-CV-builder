from flask import Flask, request, render_template, jsonify, send_file, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import hashlib
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from fpdf import FPDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from extract_text import extract_text
from match_keywords import match_keywords
import groq
import spacy
from datetime import datetime
import uuid
import json

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cv_master_premium_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cv_master.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# PayFast configuration
PAYFAST_MERCHANT_ID = os.environ.get('PAYFAST_MERCHANT_ID', '10000100')  # Test merchant ID
PAYFAST_MERCHANT_KEY = os.environ.get('PAYFAST_MERCHANT_KEY', '46f0cd694581a')  # Test merchant key
PAYFAST_PASSPHRASE = os.environ.get('PAYFAST_PASSPHRASE', 'jt7NOE43FZPn')  # Test passphrase
PAYFAST_SANDBOX = os.environ.get('PAYFAST_SANDBOX', 'true').lower() == 'true'  # Use sandbox for testing

# Groq API Configuration
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')  # Set via environment variable
LLAMA_MODEL = "llama3-70b-8192"
client = None  # Initialize later to avoid startup hang

def get_groq_client():
    global client
    if client is None:
        try:
            client = groq.Client(api_key=GROQ_API_KEY)
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            client = None
    return client

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    cv_reports = db.relationship('CVReport', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payfast_payment_id = db.Column(db.String(100))  # PayFast payment ID
    payfast_pf_payment_id = db.Column(db.String(100))  # PayFast internal payment ID
    amount = db.Column(db.Float, nullable=False)  # Amount in ZAR
    service_type = db.Column(db.String(50), nullable=False)  # 'ats_scan' or 'cv_build'
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class CVReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    report_type = db.Column(db.String(50), nullable=False)  # 'ats_scan', 'cv_build', 'cv_enhance'
    original_filename = db.Column(db.String(255))
    ats_score = db.Column(db.Float)
    job_description = db.Column(db.Text)
    ai_suggestions = db.Column(db.Text)
    generated_cv_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create Account')

# Routes
@app.route('/')
def home():
    """Premium landing page"""
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user already exists
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with CV management"""
    user_reports = CVReport.query.filter_by(user_id=current_user.id).order_by(CVReport.created_at.desc()).all()
    return render_template('dashboard.html', reports=user_reports)

@app.route('/scan', methods=['GET', 'POST'])
@login_required
def ats_scan():
    """ATS Scanning service"""
    if request.method == 'POST':
        # Handle file upload and job description
        if 'cv_file' not in request.files or 'job_description' not in request.form:
            flash('Please upload a resume and provide a job description.', 'error')
            return redirect(url_for('ats_scan'))
        
        resume = request.files['cv_file']
        job_description = request.form['job_description'].strip()
        
        if resume.filename == '' or not job_description:
            flash('Please upload a resume and provide a job description.', 'error')
            return redirect(url_for('ats_scan'))
        
        # Save uploaded file
        filename = secure_filename(resume.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
        resume.save(file_path)
        
        try:
            # Extract text and calculate ATS score
            resume_text = extract_text(file_path)
            score, matches = match_keywords(resume_text, job_description)
            
            # Create CV report (unpaid initially)
            report = CVReport(
                user_id=current_user.id,
                report_type='ats_scan',
                original_filename=filename,
                ats_score=score,
                job_description=job_description,
                is_paid=False
            )
            db.session.add(report)
            db.session.commit()
            
            # Store in session for payment
            session['pending_report_id'] = report.id
            session['service_type'] = 'ats_scan'
            
            return redirect(url_for('payment', service='ats_scan'))
            
        except Exception as e:
            flash(f'Error processing resume: {str(e)}', 'error')
            return redirect(url_for('ats_scan'))
    
    return render_template('scan.html')

@app.route('/build')
@login_required
def cv_builder():
    """CV Builder service"""
    return render_template('cv_builder.html')

@app.route('/build', methods=['POST'])
@login_required
def process_cv_build():
    """Process CV building request"""
    data = request.get_json()
    
    # Extract user input data
    personal_info = data.get('personal_info', {})
    experience = data.get('experience', [])
    education = data.get('education', [])
    skills = data.get('skills', [])
    job_description = data.get('job_description', '')
    
    # Create CV report (unpaid initially)
    report = CVReport(
        user_id=current_user.id,
        report_type='cv_build',
        job_description=job_description,
        is_paid=False
    )
    db.session.add(report)
    db.session.commit()
    
    # Store data in session for payment
    session['pending_report_id'] = report.id
    session['service_type'] = 'cv_build'
    session['cv_data'] = {
        'personal_info': personal_info,
        'experience': experience,
        'education': education,
        'skills': skills,
        'job_description': job_description
    }
    
    return jsonify({'redirect': url_for('payment', service='cv_build')})

def generate_payfast_signature(data, passphrase=None):
    """Generate PayFast signature for data validation"""
    # Create parameter string
    param_string = '&'.join([f'{key}={urllib.parse.quote_plus(str(value))}' for key, value in sorted(data.items()) if value != ''])
    
    # Add passphrase if provided
    if passphrase:
        param_string += f'&passphrase={urllib.parse.quote_plus(passphrase)}'
    
    # Generate MD5 hash
    return hashlib.md5(param_string.encode()).hexdigest()

@app.route('/payment/<service>')
@login_required
def payment(service):
    """Payment page for services"""
    if service not in ['ats_scan', 'cv_build']:
        flash('Invalid service type.', 'error')
        return redirect(url_for('dashboard'))
    
    amount = 35.00  # R35 for both services
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        amount=amount,
        service_type=service,
        status='pending'
    )
    db.session.add(transaction)
    db.session.commit()
    
    # PayFast payment data
    payment_data = {
        'merchant_id': PAYFAST_MERCHANT_ID,
        'merchant_key': PAYFAST_MERCHANT_KEY,
        'return_url': url_for('payment_success', _external=True),
        'cancel_url': url_for('payment_cancel', _external=True),
        'notify_url': url_for('payment_notify', _external=True),
        'name_first': current_user.first_name,
        'name_last': current_user.last_name,
        'email_address': current_user.email,
        'item_name': f'CV Master - {service.replace("_", " ").title()}',
        'item_description': f'{service.replace("_", " ").title()} service',
        'amount': f'{amount:.2f}',
        'custom_int1': transaction.id,
        'custom_str1': service
    }
    
    # Generate signature
    signature = generate_payfast_signature(payment_data, PAYFAST_PASSPHRASE if not PAYFAST_SANDBOX else None)
    payment_data['signature'] = signature
    
    # PayFast URL
    payfast_url = 'https://sandbox.payfast.co.za/eng/process' if PAYFAST_SANDBOX else 'https://www.payfast.co.za/eng/process'
    
    return render_template('payment.html', 
                         service=service, 
                         amount=amount,
                         payment_data=payment_data,
                         payfast_url=payfast_url)

@app.route('/payment/success')
@login_required
def payment_success():
    """PayFast payment success callback"""
    flash('Payment successful! Processing your request...', 'success')
    return redirect(url_for('dashboard'))

@app.route('/payment/cancel')
@login_required
def payment_cancel():
    """PayFast payment cancel callback"""
    flash('Payment was cancelled.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/payment/notify', methods=['POST'])
def payment_notify():
    """PayFast ITN (Instant Transaction Notification) handler"""
    try:
        # Get POST data
        post_data = dict(request.form)
        
        # Verify signature
        signature = post_data.pop('signature', None)
        calculated_signature = generate_payfast_signature(post_data, PAYFAST_PASSPHRASE if not PAYFAST_SANDBOX else None)
        
        if signature != calculated_signature:
            return 'Invalid signature', 400
        
        # Get transaction
        transaction_id = post_data.get('custom_int1')
        if not transaction_id:
            return 'No transaction ID', 400
            
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return 'Transaction not found', 404
        
        # Update transaction status
        payment_status = post_data.get('payment_status')
        if payment_status == 'COMPLETE':
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            transaction.payfast_payment_id = post_data.get('payment_id')
            transaction.payfast_pf_payment_id = post_data.get('pf_payment_id')
            
            # Process the service based on transaction type
            if transaction.service_type == 'ats_scan':
                # Mark report as paid and generate AI suggestions
                report = CVReport.query.filter_by(
                    user_id=transaction.user_id,
                    is_paid=False
                ).order_by(CVReport.created_at.desc()).first()
                if report:
                    report.is_paid = True
                    report.transaction_id = transaction.id
                    # Generate AI suggestions here if needed
                    
            elif transaction.service_type == 'cv_build':
                # Process CV building
                pass
                
        else:
            transaction.status = 'failed'
        
        db.session.commit()
        return 'OK', 200
        
    except Exception as e:
        print(f'PayFast notification error: {e}')
        return 'Error', 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download/<int:report_id>')
@login_required
def download(report_id):
    """Download page for completed reports"""
    report = CVReport.query.filter_by(id=report_id, user_id=current_user.id, is_paid=True).first()
    if not report:
        flash('Report not found or not paid for.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('download.html', report=report)

@app.route('/download-file/<int:report_id>')
@login_required
def download_file(report_id):
    """Download the actual file"""
    report = CVReport.query.filter_by(id=report_id, user_id=current_user.id, is_paid=True).first()
    if not report:
        return "File not found or not authorized", 404
    
    if report.report_type == 'cv_build' and report.generated_cv_path:
        return send_file(report.generated_cv_path, as_attachment=True)
    else:
        # Generate ATS report PDF
        pdf_path = generate_ats_report_pdf(report)
        return send_file(pdf_path, as_attachment=True)

# AI Helper Functions
def generate_ats_suggestions(job_description, ats_score):
    """Generate AI suggestions for ATS improvement"""
    try:
        client = get_groq_client()
        if not client:
            return "AI service temporarily unavailable. Please try again later."
            
        prompt = f"""
Analyze this job description and provide specific suggestions to improve ATS compatibility for a CV that scored {ats_score}%:

Job Description:
{job_description}

Provide:
1. Missing keywords that should be included
2. Skills that should be emphasized
3. Specific phrasing recommendations
4. Industry-specific terms to include
5. Action verbs that would improve the CV

Format the response as actionable recommendations.
"""
        
        completion = client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
            top_p=1,
        )
        
        return completion.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating suggestions: {str(e)}"

def generate_cv_content(cv_data):
    """Generate AI-optimized CV content"""
    try:
        client = get_groq_client()
        if not client:
            return "AI service temporarily unavailable. Please try again later."
            
        prompt = f"""
Create a professional, ATS-optimized CV based on this information:

Personal Information: {cv_data.get('personal_info', {})}
Work Experience: {cv_data.get('experience', [])}
Education: {cv_data.get('education', [])}
Skills: {cv_data.get('skills', [])}
Target Job: {cv_data.get('job_description', '')}

Format as a complete, professional CV with:
- Professional summary
- Work experience with quantified achievements
- Education section
- Skills section with relevant keywords
- ATS-friendly formatting

Make it compelling and keyword-rich for the target role.
"""
        
        completion = client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2500,
            top_p=1,
        )
        
        return completion.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating CV: {str(e)}"

def generate_cv_pdf(content, user_id):
    """Generate professional PDF from CV content"""
    filename = f"cv_{user_id}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor='#2C3E50'
    )
    
    # Split content into paragraphs and format
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            p = Paragraph(para.strip(), styles['Normal'])
            story.append(p)
            story.append(Spacer(1, 12))
    
    doc.build(story)
    return filepath

def generate_ats_report_pdf(report):
    """Generate ATS analysis report PDF"""
    filename = f"ats_report_{report.user_id}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("ATS Compatibility Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Score
    score_text = f"ATS Score: {report.ats_score}%"
    score = Paragraph(score_text, styles['Heading2'])
    story.append(score)
    story.append(Spacer(1, 20))
    
    # Suggestions
    if report.ai_suggestions:
        suggestions_title = Paragraph("AI Recommendations:", styles['Heading3'])
        story.append(suggestions_title)
        story.append(Spacer(1, 12))
        
        suggestions = Paragraph(report.ai_suggestions, styles['Normal'])
        story.append(suggestions)
    
    doc.build(story)
    return filepath

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
