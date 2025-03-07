def extract_keywords(text):
    # Simple keyword extraction based on word frequency
    words = text.lower().split()
    # Remove common words and punctuation
    stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it',
                 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'}
    
    keywords = [word.strip('.,!?()[]{}":;') for word in words if word not in stop_words and len(word) > 2]
    return list(set(keywords))