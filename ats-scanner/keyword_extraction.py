import spacy
import re
from collections import Counter

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    """Enhanced keyword extraction for better ATS matching"""
    if not text:
        return set()
    
    text_lower = text.lower()
    doc = nlp(text_lower)
    keywords = set()
    
    # 1. Extract single words (lemmatized, excluding stop words)
    for token in doc:
        if (token.is_alpha and not token.is_stop and len(token.text) > 2 and 
            token.pos_ in ['NOUN', 'ADJ', 'VERB', 'PROPN']):
            keywords.add(token.lemma_)
    
    # 2. Extract technical terms and proper nouns (preserve original case)
    tech_pattern = r'\b[A-Z][a-zA-Z]*(?:\+{1,2}|#)?\b|\b[a-zA-Z]+(?:\.[a-zA-Z]+)+\b'
    tech_terms = re.findall(tech_pattern, text)
    for term in tech_terms:
        if len(term) > 2:
            keywords.add(term.lower())
    
    # 3. Extract multi-word phrases (2-3 words)
    phrases = []
    for i in range(len(doc) - 1):
        if (not doc[i].is_stop and not doc[i+1].is_stop and 
            doc[i].is_alpha and doc[i+1].is_alpha):
            phrase = f"{doc[i].lemma_} {doc[i+1].lemma_}"
            phrases.append(phrase)
            
            # 3-word phrases
            if i < len(doc) - 2 and not doc[i+2].is_stop and doc[i+2].is_alpha:
                phrase3 = f"{doc[i].lemma_} {doc[i+1].lemma_} {doc[i+2].lemma_}"
                phrases.append(phrase3)
    
    # Add common phrases
    phrase_counts = Counter(phrases)
    for phrase, count in phrase_counts.items():
        if count >= 1 and len(phrase.split()) <= 3:
            keywords.add(phrase)
    
    # 4. Extract years of experience patterns
    exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)'
    exp_matches = re.findall(exp_pattern, text_lower)
    for match in exp_matches:
        keywords.add(f"{match} years experience")
        keywords.add(f"{match} years")
    
    # 5. Extract certifications and degrees
    cert_pattern = r'\b(?:certified|certification|degree|bachelor|master|phd|mba|cpa|pmp|cissp|aws|azure|google)\b'
    cert_matches = re.findall(cert_pattern, text_lower)
    keywords.update(cert_matches)
    
    # 6. Extract programming languages and technologies
    tech_keywords = {
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node', 'sql', 'mysql', 'postgresql',
        'mongodb', 'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'jenkins', 'ci/cd',
        'agile', 'scrum', 'devops', 'machine learning', 'ai', 'data science', 'analytics', 'tableau',
        'power bi', 'excel', 'salesforce', 'sap', 'oracle', 'microsoft', 'adobe', 'figma', 'sketch'
    }
    
    for word in text_lower.split():
        if word in tech_keywords:
            keywords.add(word)
    
    return keywords