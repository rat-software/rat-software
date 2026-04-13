'''
This classifier enables the user to input a webpage html to calculate its readability based on different scores.
It is able to differentiate between English and German pages.
'''

from langdetect import detect, LangDetectException
import textstat
from bs4 import BeautifulSoup

class TextAnalyzer:
    def __init__(self) -> None:
        pass  

    def analyzeEn(self, main_text):
        """Calculates and returns only the Flesch Reading Ease for English text."""
        textstat.set_lang("en_US")
        return textstat.flesch_reading_ease(main_text)
        
    def analyzeDe(self, main_text):
        """Calculates and returns only the Flesch Reading Ease for German text."""
        textstat.set_lang("de_DE")
        return textstat.flesch_reading_ease(main_text)

    def analyze(self, html_code):
        """
        Analyzes HTML code, extracts text, detects the language, and returns the 
        Flesch Reading Ease score directly.
        
        Returns:
            float: The readability score.
            str: A status message if analysis is not possible.
        """
        soup = BeautifulSoup(html_code, features="lxml")
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        main_text = soup.get_text(separator=' ', strip=True)

        # Check for a minimum word count to ensure meaningful analysis
        if len(main_text.split()) < 100:
            return "error"
        
        try:
            lang = detect(main_text)
            if lang == "en":
                return self.analyzeEn(main_text)
            elif lang == "de":
                return self.analyzeDe(main_text)
            else:
                return f"Language '{lang}' not supported"
        except LangDetectException:
            return "Language could not be detected"