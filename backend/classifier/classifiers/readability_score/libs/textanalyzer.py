'''
This classifier enables the user to input a webpage html to calculate its readability based on different scores.
It is able to differentiate between English, German and Arabic pages.
'''


#Main functions 

from langdetect import detect
import textstat

from bs4 import BeautifulSoup



class TextAnalyzer:
    def __init__(self) -> None:
        pass  

    def analyzeEn(self, main_text):
        textstat.set_lang("en")

        # Calculate readability scores
        flesch_reading_ease = textstat.flesch_reading_ease(main_text)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(main_text)
        standard_deviation = textstat.text_standard(main_text, float_output=False)

        # Calculate reading time
        reading_time = round(textstat.reading_time(main_text, ms_per_char=14.69) / 60, 1)

        return {"Language": "English", "Reading Ease":flesch_reading_ease, "Grade":flesch_kincaid_grade, "Standard Deviation":standard_deviation, "Reading Time":reading_time}
        
    def analyzeDe(self, main_text):
        textstat.set_lang("de")
        
        # Calculate readability scores
        flesch_reading_ease = textstat.flesch_reading_ease(main_text)
        wiener_sachtextformel_grade = textstat.wiener_sachtextformel(main_text, 1)
        standard_deviation = textstat.text_standard(main_text, float_output=False)

        # Calculate reading time
        reading_time = round(textstat.reading_time(main_text, ms_per_char=14.69) / 60, 1)

        return {"Language": "Deutsch", "Reading Ease":flesch_reading_ease, "Grade":wiener_sachtextformel_grade, "Standard Deviation":standard_deviation, "Reading Time":reading_time}


        
        
    def analyze(self, main_text):
        soup = BeautifulSoup(main_text, features="lxml")
        main_text = soup.get_text()
        lang = detect(main_text)
        if lang == "en":
            indicators = self.analyzeEn(main_text)
        elif lang == "de":
            indicators = self.analyzeDe(main_text)

        else:
            indicators = "No language detected"

        return indicators