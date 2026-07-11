import re
import emoji
class TextPreprocessor():

    def __init__(self):
        pass


    def preprocess(self, text:str):
        if not text or not isinstance(text, str):
            return ""

        text_without_emojis = emoji.replace_emoji(text, replace='')

        clean_text = re.sub(r'\s+', ' ', text_without_emojis).strip()

        return clean_text