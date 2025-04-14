#nltk_download.py

nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
import nltk

# Check if 'punkt' is already downloaded; if not, download it
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
