import json

import spacy
from nltk.stem.snowball import SnowballStemmer
import regex as re

nlp = spacy.load("en_core_web_sm")
# print("Pipeline:", nlp.pipe_names)
# text = "you are play football"
# text = "he is play football"
# text = "he is play football"
# text = "ahmad is drive the car"
# text = "i am playing football yesterday"
# text = "i was play football now"
text1 = "i am good tomorrow"
text2 = "he is played football and players play tennis next week"
# text = "i see movie yesterday"
examples = [nlp(text1.lower()), nlp(text2.lower())]


# verb_map = {"see": "saw", "go": "went", "is": "was", "am": "was", "are": "were"}

class CorrectVerb:

    def __init__(self):
        f = open("verbs-all.json")
        verbs = json.load(f)
        self.present_to_past_map = {v[0]: v[2] for v in verbs}
        # self.present_to_past_map["am"] = "was"
        # self.present_to_past_map["is"] = "was"
        # self.present_to_past_map["are"] = "were"

        self.past_to_present_map = dict((y, x) for x, y in self.present_to_past_map.items())

        self.all_verb_to_be = ("am", "is", "are", "was", "were")
        self.present_verb_to_be = ("am", "is", "are")
        self.past_verb_to_be = ("was", "were")
        self.singular_pronouns = ("he", "she", "it")
        self.plural_pronouns = ("we", "they", "you")

    def replace(self, text, r1, r2):
        return " ".join(list(map(lambda t: re.sub(fr"^{r1}$", r2, t), text.split())))

    def correct(self, doc):
        verbs = self.get_all_verbs(doc)
        print("the sentence before correction : ", doc.text)
        corrected_text = self.correct_to_simple_past(doc, verbs)
        print("the sentence after simple past correction : ", corrected_text)
        corrected_text = self.correct_to_past_cont(nlp(corrected_text), verbs)
        print("the sentence after past cont && simple past correction : ", corrected_text)
        corrected_text = self.correct_to_past_cont(doc, verbs)
        print("the sentence after past cont correction : ", corrected_text)
        corrected_text = self.correct_to_present_cont(doc, verbs)
        print("the sentence after present cont correction : ", corrected_text)
        corrected_text = self.correct_to_future(doc, verbs)
        print("the sentence after future correction : ", corrected_text)

        return corrected_text

    def get_all_verbs(self, doc):
        verbs = []
        prev = None
        for token in doc:
            print(token.text, " ", token.morph.to_dict())  # Printing the morphological features in dictionary format.
            if len(token.morph.get("VerbForm")) != 0:
                verb = {"verb": token.text, "form": token.morph.get("VerbForm"), "tense": token.morph.get("Tense"),
                        "lemma": token.lemma_}
                verbs.append((verb, prev))
                prev = verb
            else:
                prev = {'noun': token.text, "number": token.morph.get("Number")}
        print(verbs)
        print()
        return verbs

    def get_past_form(self, verb):
        return self.present_to_past_map.get(verb['verb'], verb["lemma"] + "ed")

    def correct_to_simple_past(self, doc, verbs):
        past_keywords = [
            'yesterday',
            'before',
            'last',
            'this morning',
            'ago'
        ]
        text = doc.text
        past_signal = any(past_word in text for past_word in past_keywords)
        if past_signal:
            for i, (current, prev) in enumerate(verbs):
                # if current is verb to be and the next word is verb continue else replace
                if current['form'][0] == 'Fin' and current['verb'] in self.all_verb_to_be:
                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        if c == current and 'verb' in next.keys():
                            continue

                    text = self.replace(text, current['verb'], self.get_past_form(current))
                elif current['form'][0] == 'Fin' and current['verb'] == 'will':
                    continue
                # Fin -> with s , Inf -> without s, Part  -> ing | ed
                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    # if prev is verb to be or will
                    # if 'verb' in prev.keys() and (prev['verb'] in self.all_verb_to_be or prev['verb'] == 'will'):
                    #     text = text.replace(f"{prev['verb']} {current['verb']}",
                    #                         self.get_past_form(current))
                    if 'verb' in prev.keys():
                        if prev['verb'] == 'will':
                            text = text.replace(f"{prev['verb']} {current['verb']}",
                                                self.get_past_form(current))
                    else:
                        text = self.replace(text, current['verb'], self.get_past_form(current))
        return text

    def correct_to_past_cont(self, doc, verbs):
        past_keywords = [
            'yesterday',
            'before',  # the day before
            'last',
            'this morning',
            'ago'
        ]

        text = doc.text
        past_signal = any(past_word in text for past_word in past_keywords)
        if past_signal:
            for i, (current, prev) in enumerate(verbs):
                if current['form'][0] == 'Fin' and current['verb'] in self.all_verb_to_be or current['verb'] == 'will':
                    # if prev word is noun replace verb to be to suitable one else delete
                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        if 'noun' in prev.keys():
                            verb_to_be = 'was' if prev['number'][0] == 'Sing' else "were"
                        else:
                            verb_to_be = ""
                        if c == current and 'verb' in next.keys():
                            text = text.replace(f"{current['verb']} {next['verb']}", f"{verb_to_be} {next['lemma']}ing")
                            verbs.pop(i + 1)

                # elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                #     if 'noun' in prev.keys():
                #         verb_to_be = 'was' if prev['number'][0] == 'Sing' else "were"
                #         text = self.replace(text, current['verb'], f"{verb_to_be} {current['lemma']}ing")
        return text

    def correct_to_present_cont(self, doc, verbs):
        present_keywords = ['now', 'at the moment', 'today']

        text = doc.text
        present_signal = any(present_word in text for present_word in present_keywords)

        if present_signal:
            for i, (current, prev) in enumerate(verbs):
                if current['form'][0] == 'Fin' and current['verb'] in self.all_verb_to_be or current['verb'] == 'will':
                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        # if prev word is noun replace verb to be to suitable one else delete
                        if 'noun' in prev.keys():
                            verb_to_be = 'am' if prev['noun'] == 'i' else 'is' if prev['number'][0] == 'Sing' else "are"
                        else:
                            verb_to_be = ""
                        if c == current and 'verb' in next.keys():
                            text = text.replace(f"{current['verb']} {next['verb']}", f"{verb_to_be} {next['lemma']}ing")
                            verbs.pop(i + 1)

                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    if 'noun' in prev.keys():
                        verb_to_be = 'am' if prev['noun'] == 'i' else 'is' if prev['number'][0] == 'Sing' else "are"
                        text = self.replace(text, current['verb'], f"{verb_to_be} {current['lemma']}ing")

        return text

    def correct_to_future(self, doc, verbs):
        future_keywords = ['tomorrow', 'next']
        text = doc.text
        future_signal = any(future_keyword in text for future_keyword in future_keywords)

        if future_signal:
            for i, (current, prev) in enumerate(verbs):
                # if current is verb to be and the next word is verb continue else replace
                if current['form'][0] == 'Fin' and current['verb'] in self.all_verb_to_be:
                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        if c == current and 'verb' in next.keys():
                            continue
                    text = self.replace(text, current['verb'], f"will {current['lemma']}")
                elif current['form'][0] == 'Fin' and current['verb'] == 'will':
                    continue
                # Fin -> with s , Inf -> without s, Part  -> ing | ed
                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    # if prev is verb to be or will
                    if 'verb' in prev.keys() and (prev['verb'] in self.all_verb_to_be or prev['verb'] == 'will'):
                        text = text.replace(f"{prev['verb']} {current['verb']}",
                                            f"will {current['lemma']}")
                    else:
                        prev_word = prev['noun'] if 'noun' in prev.keys() else prev['verb']
                        text = text.replace(f"{prev_word} {current['verb']}", f"{prev_word} will {current['lemma']}")
            return text


c = CorrectVerb()

for example in examples:
    correct = c.correct(example)
    print()
