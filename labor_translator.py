from transformers import pipeline

class LaborTranslator:
    def __init__(self):
        self.translator = pipeline("translation", model="Helsinki-NLP/opus-mt-ar-en")

    def translate(self, text):
        if len(text) > 512:
            text = text[:512]
        return self.translator(text, max_length=512)[0]['translation_text']