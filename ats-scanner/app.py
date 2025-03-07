from flask import Flask, request, render_template, jsonify, send_file, session
from extract_text import extract_text_from_file
from keyword_extraction import extract_keywords
from fpdf import FPDF
import os
import groq
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')  # Change this in production

# Initialize Groq client
if not os.environ.get('GROQ_API_KEY'):
    print("Warning: GROQ_API_KEY environment variable is not set. AI features will not work.")
    client = None
else:
    client = groq.Groq()

def analyze_resume(resume_text, job_description):
    """Analyze resume against job description using Groq API."""
    if not client:
        return {'score': 75, 'analysis': 'AI analysis unavailable - API key not configured', 
                'missing_elements': ['API key not configured'], 
                'suggestions': ['Please configure GROQ_API_KEY to enable AI features']}

    prompt = f"""You are an expert ATS (Applicant Tracking System) and resume analyzer. 
    Analyze the following resume against the job description and provide:
    1. A score out of 100
    2. A detailed analysis of the match
    3. Key missing elements
    4. Specific improvement suggestions

    Job Description:
    {job_description}

    Resume:
    {resume_text}

    Provide the response in JSON format with these keys:
    - score: number
    - analysis: string (detailed analysis)
    - missing_elements: list of strings
    - suggestions: list of strings
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.5,
            max_tokens=2000
        )
        
        response = chat_completion.choices[0].message.content
        return json.loads(response)
    except Exception as e:
        print(f"Error in AI analysis: {str(e)}")
        return None

def optimize_resume(resume_text, job_description):
    """Generate optimization suggestions using Groq API."""
    if not client:
        return "AI optimization unavailable - Please configure GROQ_API_KEY to enable AI features"

    prompt = f"""As an expert resume writer and ATS optimization specialist, provide detailed suggestions 
    to optimize this resume for the given job description. Focus on:
    1. Content improvements
    2. Format optimization
    3. Keyword optimization
    4. Specific phrases to add
    5. Structure recommendations

    Job Description:
    {job_description}

    Resume:
    {resume_text}

    Provide very specific, actionable suggestions that will help improve the resume's ATS score.
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=2000
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error in optimization: {str(e)}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'})
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})

        job_description = request.form.get('job_description', '')
        
        # Extract text from the uploaded file
        resume_text = extract_text_from_file(file)
        
        # Store in session
        session['resume_text'] = resume_text
        session['job_description'] = job_description
        
        # Perform AI analysis
        analysis_result = analyze_resume(resume_text, job_description)
        score = analysis_result['score'] if analysis_result else 75
        
        return render_template('index.html',
                             resume_text=resume_text,
                             job_description=job_description,
                             score=score)
    
    return render_template('index.html')

@app.route('/generate-ai', methods=['POST'])
def generate_ai():
    data = request.json
    field = data.get('field')
    job_description = data.get('job_description', '')
    resume_text = data.get('resume_text', '')
    
    if not resume_text or not job_description:
        return jsonify({'error': 'Missing resume text or job description'})
    
    if field == "analyze":
        analysis_result = analyze_resume(resume_text, job_description)
        if analysis_result:
            return jsonify({
                'suggestion': f"""ATS Analysis Results:

Score: {analysis_result['score']}/100

Detailed Analysis:
{analysis_result['analysis']}

Missing Elements:
{"".join(['• ' + elem + '\n' for elem in analysis_result['missing_elements']])}

Improvement Suggestions:
{"".join(['• ' + elem + '\n' for elem in analysis_result['suggestions']])}"""
            })
        else:
            return jsonify({'error': 'Failed to analyze resume'})
    else:
        optimization = optimize_resume(resume_text, job_description)
        if optimization:
            return jsonify({'suggestion': optimization})
        else:
            return jsonify({'error': 'Failed to generate optimization suggestions'})

@app.route('/download-optimized-cv', methods=['POST'])
def download_optimized_cv():
    content = request.json.get('content', '')
    
    # Create a PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)
    
    # Split content into lines and add to PDF
    lines = content.split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, txt=line)
    
    # Save PDF to a temporary file
    temp_file = 'Optimized_CV.pdf'
    pdf.output(temp_file)
    
    try:
        return send_file(temp_file, as_attachment=True)
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

@app.route('/clear-session', methods=['GET'])
def clear_session():
    session.clear()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
