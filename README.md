# ATS Resume Scanner

AI Powered ATS Resume Scanner is an open-source web application that helps job seekers optimize their resumes for 
Applicant Tracking Systems (ATS).The application extracts text from resumes, matches keywords from job 
descriptions, and provides AI-generated suggestions for improvement.

## 🚀 Features
- Upload a resume (PDF, DOCX)
- Extract and analyze resume text
- Match keywords with a job description
- Generate AI-powered suggestions to optimize resumes
- Download an optimized resume in PDF format

## 📌 Live Demo
Check out the deployed version of the project:
[ATS Resume Scanner]([https://your-deployment-url.com](https://ats-friendly-cv-builder-production.up.railway.app/))

## 🛠 Tech Stack
- Python (Flask)
- SpaCy (NLP for text extraction and keyword matching)
- Groq AI (LLama3-based AI suggestions)
- HTML, CSS, JavaScript (Frontend)
- FPDF (For generating optimized PDFs)

## 📂 Project Structure
```
ats-scanner/
│── static/          # CSS, JavaScript, and other static files
│── templates/       # HTML templates
│── uploads/         # Uploaded resume files
│── app.py           # Main Flask application
│── extract_text.py  # Extracts text from resumes
│── match_keywords.py # Matches keywords between resume & job description
│── requirements.txt  # Python dependencies
│── Procfile         # Deployment configuration
│── vercel.json      # Vercel deployment config (if applicable)
│── README.md        # Project documentation
```

## 🔧 Installation & Usage
### 1️⃣ Clone the Repository
```sh
git clone https://github.com/innowave620/ats-scanner.git
cd ats-scanner
```

### 2️⃣ Set Up a Virtual Environment (Recommended)
```sh
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 4️⃣ Run the Flask Application
```sh
python app.py
```
The app should now be running on `http://127.0.0.1:5000`

### 5️⃣ Deployment
#### Deploy on Railway
- Ensure the `PORT` environment variable is set.
- Deploy using Railway’s CLI or Web Dashboard.

#### Deploy on Vercel
- Use the provided `vercel.json` configuration.
- Run:
```sh
vercel --prod
```

## 🤝 Contributing
We welcome contributions! To contribute:
1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes and commit (`git commit -m 'Add new feature'`)
4. Push to your branch (`git push origin feature-branch`)
5. Open a pull request

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙌 Acknowledgments
- Open-source libraries: Flask, SpaCy, Groq AI
- Community contributions

---
Made with ❤️ by Senzo Calvin Shinga from [innowave620](https://github.com/innowave620)

