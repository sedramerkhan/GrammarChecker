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
text1 = "i will watch movie yesterday"
text2 = "he is played football and players were play tennis ago"
# text = "i see movie yesterday"
examples = [nlp(text1.lower()), nlp(text2.lower())]


# verb_map = {"see": "saw", "go": "went", "is": "was", "am": "was", "are": "were"}

class CorrectVerb:

    def __init__(self):
        f = open("verbs-all.json")
        verbs = json.load(f)
        self.present_to_past_map = {v[0]: v[2] for v in verbs}
        self.present_to_past_map["am"] = "was"
        self.present_to_past_map["is"] = "was"
        self.present_to_past_map["are"] = "were"

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
        corrected_text = self.correct_to_simple_past(doc, verbs)
        # corrected_text = self.correct_to_past_cont(doc,verbs)
        return corrected_text

    def get_all_verbs(self, doc):
        verbs = []
        prev = None
        for token in doc:
            print(token.text, " ", token.morph.to_dict())  # Printing the morphological features in dictionary format.

            # features such as Number(Singular or plural).
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
                    if 'verb' in prev.keys() and prev['verb'] in self.all_verb_to_be or prev['verb'] == 'will':
                        text = text.replace(f"{prev['verb']} {current['verb']}",
                                            self.get_past_form(current))
                    else:
                        text = self.replace(current['verb'], self.get_past_form(current))
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
                    if 'noun' in prev.keys():
                        verb_to_be = 'was' if prev['number'][0] == 'Sing' else "were"
                        text = self.replace(text, current['verb'], verb_to_be)
                    else:
                        text = self.replace(text, current['verb'], "")

                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        if c == current and 'verb' in next.keys():
                            text = self.replace(text, next['verb'], next['lemma'] + "ing")
                            verbs.pop(i + 1)

                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    if 'noun' in prev.keys():
                        verb_to_be = 'was' if prev['number'][0] == 'Sing' else "were"
                        text = self.replace(text, current['verb'], f"{verb_to_be} {current['lemma']}ing")

                # elif current['form'][0] in ('Fin', 'Inf'):  # Fin -> with s , Inf -> without s
                #     infinitive_or_verb_s = (current['verb'], current['lemma'])
                #     print("simple present", infinitive_or_verb_s)
                # elif current['form'][0] == 'Part' and current['tense'][0] == 'Pres':
                #     verb_ing = (current['verb'], current['lemma'])
                #     print(verb_ing)
                # elif current['form'][0] == 'Part' and current['tense'][0] == 'Past':
                #     verb_ed = (current['verb'], current['lemma'])
                #     print(verb_ed)
                #
                # if past_signal:
                #     if verb_to_be is not None:
                #         if verb_to_be in self.present_verb_to_be:
                #             text = self.replace(text, verb_to_be,
                #                                 self.present_to_past_map.get(verb_to_be, verb_to_be + "ed"))
                #         if infinitive_or_verb_s is not None:
                #             text = self.replace(text, infinitive_or_verb_s[0], infinitive_or_verb_s[1] + "ing")
                #
                #         if verb_ed is not None:
                #             text = self.replace(text, verb_ed[0], verb_ed[1] + "ing")
                #     else:
                #         pass  # todo:
        return text

    def correct_to_present_cont(self, doc, verbs):
        present_keywords = ['now', 'at the moment']
        verb_to_be = None
        infinitive_or_verb_s = None
        verb_ed = None

        text = doc.text
        present_signal = any(present_word in text for present_word in present_keywords)

        for verb in verbs:
            if verb['form'][0] == 'Fin' and verb['verb'] in self.all_verb_to_be:
                verb_to_be = verb['verb']
            elif verb['form'][0] in ('Fin', 'Inf'):  # Fin -> with s , Inf -> without s
                infinitive_or_verb_s = (verb['verb'], verb['lemma'])
            elif verb['form'][0] == 'Part' and verb['tense'][0] == 'Past':
                verb_ed = (verb['verb'], verb['lemma'])

            if present_signal:
                if verb_to_be is not None:
                    if verb_to_be in self.past_verb_to_be:
                        if any(letter in text.split() for letter in ("i", "I")):
                            new_verb_to_be = 'am'
                        else:
                            new_verb_to_be = self.past_to_present_map[verb_to_be]
                        text = self.replace(text, verb_to_be, new_verb_to_be)
                    if infinitive_or_verb_s is not None:
                        text = self.replace(text, infinitive_or_verb_s[0], infinitive_or_verb_s[1] + 'ing')
                    if verb_ed is not None:
                        text = self.replace(text, verb_ed[0], verb_ed[1] + 'ing')
                else:
                    pass  # todo:

        return text

    def correct_to_future(self, doc, verbs):
        stemmer = SnowballStemmer(language='english')
        present_words = [
            'tomorrow',
            'next week',
            'next year',
            'the day after tomorrow'
        ]
        toBe = None
        will = None
        simplePresent = None
        simplePast = None
        verbs = []
        furureSignal = False
        text = doc.text
        for i in present_words:
            if i in text:
                furureSignal = True
                break
        for token in doc:
            print(token.text)
            # print(token.lemma_)
            # print(token.morph)   # Printing all the morphological features.
            print(token.morph.get("VerbForm"))  # Printing a particular type of morphological
            # features such as Number(Singular or plural).
            if len(token.morph.get("VerbForm")) != 0:
                verbs.append(
                    {"verb": token.text, "form": token.morph.get("VerbForm"), "tense": token.morph.get("Tense")})
            print(token.morph.to_dict())  # Printing the morphological features in dictionary format.
            print('\n\n')
        print(verbs)
        for verb in verbs:
            if verb['form'][0] == 'Fin':
                if verb['verb'] == 'will':
                    will = verb['verb']
            elif verb['form'][0] == 'Inf':
                if verb['verb'] in ['is', 'am', 'are', 'was', 'were']:
                    toBe = verb['verb']
                    print(toBe)
            elif verb['form'][0] == 'Part' and verb['tense'][0] == 'Past':
                simplePast = verb['verb']
                print(simplePast)

        if furureSignal and will:
            if toBe is not None:
                correct = text.replace(toBe, 'be')
                return correct
            elif simplePast is not None:
                correct = text.replace(simplePast, stemmer.stem(simplePast))
                return correct

        else:
            doc.text


c = CorrectVerb()

for example in examples:
    correct = c.correct(example)
    print("the sentence before correction : ", example)
    print("the sentence after correction : ", correct)
    print()
