ats-scanner/                     # Root project folder
│── app.py                        # Main Flask app (backend)
│── extract_text.py               # Extract text from resumes (PDF, DOCX)
│── keyword_extraction.py         # Extract keywords from job descriptions
│── match_keywords.py             # Match resume with job description
│── requirements.txt              # List of dependencies for easy installation
│
├── templates/                    # Frontend (HTML files)
│   ├── index.html                # Web interface for file upload & results
│
├── static/                       # Frontend static files
│   ├── style.css                 # CSS styles for web UI
│
├── resume_samples/               # Sample resumes for testing
│   ├── sample_resume.pdf
│   ├── sample_resume.docx
│
└── README.md                     # Documentation on how to use the project


## Environment Variables Setup

**IMPORTANT:** Before running the application, you must set up environment variables for API keys.

1. Copy the `.env` file and add your actual API keys:

```bash
# Groq API Configuration
GROQ_API_KEY=your_actual_groq_api_key_here

# PayFast Configuration (for production)
PAYFAST_MERCHANT_ID=your_actual_merchant_id
PAYFAST_MERCHANT_KEY=your_actual_merchant_key
PAYFAST_PASSPHRASE=your_actual_passphrase
PAYFAST_SANDBOX=false  # Set to true for testing
```

### Getting API Keys

**Groq API Key:**
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

**PayFast Configuration:**
1. Visit [PayFast](https://www.payfast.co.za/)
2. Sign up for a merchant account
3. Get your merchant credentials from the dashboard
4. For testing, you can use the sandbox credentials provided in the code

## Installation

Run the following command to install the necessary packages:
```bash
pip install flask pdfplumber python-docx spacy nltk python-dotenv
python -m spacy download en_core_web_sm
```

## Security Note

- Never commit your `.env` file to version control
- The `.env` file is already added to `.gitignore`
- Always use environment variables for sensitive data
