import spacy
import re
from collections import Counter

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    """Selective keyword extraction focusing on most important terms for ATS matching"""
    if not text:
        return set()
    
    text_lower = text.lower()
    doc = nlp(text_lower)
    keywords = set()
    
    # Priority keywords - technical skills, tools, frameworks
    priority_patterns = [
        r'\b(?:python|java|javascript|react|angular|vue|node|sql|mysql|postgresql|mongodb|aws|azure|docker|kubernetes|git|github|html|css|php|ruby|go|rust|swift|kotlin|flutter|django|flask|spring|laravel|tensorflow|pytorch|scikit|pandas|numpy|matplotlib|excel|powerbi|tableau|salesforce|jira|confluence|slack|teams|agile|scrum|kanban|devops|ci/cd|jenkins|terraform|ansible|linux|windows|macos|api|rest|graphql|microservices|cloud|machine learning|ai|data science|analytics|blockchain|cybersecurity|testing|automation|qa|ui/ux|figma|sketch|photoshop|illustrator|indesign|marketing|seo|sem|ppc|crm|erp|project management|leadership|communication|problem solving|analytical|creative|strategic|innovative|collaborative|detail oriented|time management|multitasking|adaptable|reliable|proactive|results driven|customer service|sales|business development|financial analysis|budgeting|forecasting|reporting|compliance|risk management|quality assurance|process improvement|training|mentoring|coaching|presentation|negotiation|conflict resolution|decision making|critical thinking|research|writing|editing|translation|multilingual|bilingual|trilingual|certification|degree|bachelor|master|phd|mba|cpa|pmp|cissp|aws certified|azure certified|google certified|microsoft certified|oracle certified|cisco certified|comptia|itil|six sigma|lean|iso|hipaa|gdpr|sox|pci|dss)\b',
        r'\b(?:[A-Z]{2,}(?:\+{1,2}|#)?|[a-zA-Z]+(?:\.[a-zA-Z]+){2,})\b'  # Acronyms and domain names
    ]
    
    # Extract priority keywords first
    for pattern in priority_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) > 1:
                keywords.add(match.lower())
    
    # Extract important nouns and adjectives (more selective)
    important_pos = ['NOUN', 'PROPN', 'ADJ']
    for token in doc:
        if (token.is_alpha and not token.is_stop and len(token.text) > 3 and 
            token.pos_ in important_pos and token.lemma_ not in ['year', 'experience', 'work', 'job', 'role', 'position', 'company', 'team', 'project', 'time', 'day', 'week', 'month', 'good', 'great', 'excellent', 'strong', 'high', 'low', 'new', 'old', 'big', 'small', 'long', 'short']):
            keywords.add(token.lemma_)
    
    # Extract critical 2-word technical phrases only
    critical_phrases = []
    for i in range(len(doc) - 1):
        if (not doc[i].is_stop and not doc[i+1].is_stop and 
            doc[i].is_alpha and doc[i+1].is_alpha and
            (doc[i].pos_ in ['NOUN', 'ADJ', 'PROPN'] or doc[i+1].pos_ in ['NOUN', 'ADJ', 'PROPN'])):
            phrase = f"{doc[i].lemma_} {doc[i+1].lemma_}"
            # Only add if it contains technical terms or important business terms
            if any(tech in phrase for tech in ['data', 'software', 'web', 'mobile', 'cloud', 'digital', 'business', 'project', 'product', 'customer', 'user', 'system', 'network', 'security', 'analysis', 'development', 'management', 'marketing', 'sales', 'finance', 'operations', 'strategy', 'design', 'research', 'quality', 'process', 'service', 'support', 'training', 'leadership', 'communication']):
                critical_phrases.append(phrase)
    
    # Add only frequently mentioned critical phrases
    phrase_counts = Counter(critical_phrases)
    for phrase, count in phrase_counts.items():
        if count >= 1:
            keywords.add(phrase)
    
    # Extract years of experience patterns
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