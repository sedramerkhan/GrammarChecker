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
text1 = "i can't play football and he can play tennis"
text1 = "he go to beach for swimming every next and last week now since "
text2 = "The players is played football and Sami watch them happily every next and last week now for 50"
# text3 = "i wants to playing tennis for go to match every next and last week now"
text3 = "i wants to playing tennis for participating in competition every next and last week now since"
# text3 = "i has seen movie every next and last week now"
examples = [nlp(text1.lower()), nlp(text2.lower()), nlp(text3)]


# verb_map = {"see": "saw", "go": "went", "is": "was", "am": "was", "are": "were"}

class CorrectVerb:

    def __init__(self):
        f = open("verbs-all.json")
        verbs = json.load(f)
        self.present_to_singular_present_map = {v[0]: v[1] for v in verbs}
        self.ing_map = {v[0]: v[4] for v in verbs}
        self.past_participle_map = {v[0]: v[3] for v in verbs}
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

        self.perfect_aux = ("has", "have", "had")

    def replace(self, text, r1, r2):
        return " ".join(list(map(lambda t: re.sub(fr"^{r1}$", r2, t), text.split())))

    def correct(self, doc):
        verbs = self.get_all_verbs(doc)

        print("the sentence before correction : ", doc.text, end="\n\n")

        corrected_text = self.correct_to_simple_present(doc, verbs)
        print("the sentence after simple present correction: ", corrected_text, end="\n\n")

        corrected_text = self.correct_to_simple_past(doc, verbs)
        # print("the sentence after simple past correction: ", corrected_text, end="\n\n")

        corrected_text = self.correct_to_past_cont(nlp(corrected_text), verbs)
        print("the sentence after past continuous && simple past correction: ", corrected_text, end="\n\n")

        # corrected_text = self.correct_to_past_cont(doc, verbs)
        # print("the sentence after past continuous correction: ", corrected_text, end="\n\n")

        corrected_text = self.correct_to_present_cont(doc, verbs)
        print("the sentence after present continuous correction: ", corrected_text, end="\n\n")

        corrected_text = self.correct_to_future(doc, verbs)
        print("the sentence after future correction: ", corrected_text, end="\n\n")

        corrected_text = self.correct_to_present_perfect(doc, verbs)
        print("the sentence after present perfect correction: ", corrected_text, end="\n\n")

        return corrected_text

    def get_all_verbs(self, doc):
        verbs = []
        prev = None
        stemmer = SnowballStemmer(language='english')
        for token in doc:
            print(token.text, " ", token.morph.to_dict(), " ", token.lemma_, " ",
                  stemmer.stem(token.text))  # Printing the morphological features in dictionary format.
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
        return self.present_to_past_map.get(verb['lemma'], verb["lemma"] + "ed")

    def get_singular_present_form(self, verb):
        return self.present_to_singular_present_map.get(verb['lemma'], verb["lemma"] + "s")

    def get_verb_ing(self, verb):
        return self.ing_map.get(verb['lemma'], verb['lemma'] + "ing")

    def get_past_participle(self, verb):
        return self.past_participle_map.get(verb['lemma'], verb['lemma'] + "ed")

    def check_to_for(self, prev, current):
        if prev['noun'] == 'to':
            return current['lemma']
        elif prev['noun'] == 'for':
            return self.get_verb_ing(current)
        return None

    def check_next_if_verb(self, verbs, i, current):
        if i < len(verbs) - 1:
            next, c = verbs[i + 1]
            if c == current and 'verb' in next.keys():
                return True
        return False

    def check_prev_if_verb(self, prev):
        return prev['verb'] in self.all_verb_to_be or prev['verb'] == 'will' or prev['verb'] in self.perfect_aux

    def correct_to_simple_present(self, doc, verbs):
        present_keywords = [
            'every',
            'each',
            'usually',
            'always',
            'often',
            'sometimes',
            'never',
        ]
        verbs = verbs.copy()
        text = doc.text
        present_signal = any(present_keyword in text for present_keyword in present_keywords)
        if present_signal:
            for i, (current, prev) in enumerate(verbs):
                # if current is verb to be and the next word is verb continue else replace
                if current['form'][0] == 'Fin' and current['verb'] in self.all_verb_to_be:
                    if self.check_next_if_verb(verbs, i, current):
                        continue

                    if 'noun' in prev.keys():
                        verb_to_be = self.check_to_for(prev, current)
                        if not verb_to_be:
                            verb_to_be = 'am' if prev['noun'] == 'i' else 'is' if prev['number'][0] == 'Sing' else "are"
                    else:
                        verb_to_be = ""
                    text = self.replace(text, current['verb'], verb_to_be)
                #     has , have ,had
                elif current['form'][0] == 'Fin' and current['verb'] in self.perfect_aux:
                    if self.check_next_if_verb(verbs, i, current):
                        continue

                    if 'noun' in prev.keys():
                        inf = current['lemma']
                        verb = self.check_to_for(prev, current)
                        if not verb:
                            verb = inf if prev['number'][0] == 'Plur' or prev['noun'] == "i" \
                                else self.get_singular_present_form(current)
                    else:
                        verb = ""
                    text = text.replace(f"{prev['noun']} {current['verb']}",
                                        f"{prev['noun']} {verb}")

                elif current['form'][0] == 'Fin' and current['verb'] == 'will':
                    continue
                # Fin -> with s , Inf -> without s, Part  -> ing | ed
                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    # if prev is verb to be or will
                    inf = current['lemma']
                    if 'verb' in prev.keys() and self.check_prev_if_verb(prev):
                        prev_prev = verbs[i - 1][1]
                        if 'noun' in prev_prev.keys():
                            verb = self.check_to_for(prev_prev, current)
                            if not verb:
                                verb = inf if prev_prev['number'][0] == 'Plur' or prev_prev['noun'] == "i" \
                                    else self.get_singular_present_form(current)
                            text = text.replace(f"{prev['verb']} {current['verb']}", verb)

                    else:
                        verb = self.check_to_for(prev, current)
                        if not verb:
                            verb = inf if prev['number'][0] == 'Plur' or prev['noun'] == "i" \
                                else self.get_singular_present_form(current)
                        text = text.replace(f"{prev['noun']} {current['verb']}", f"{prev['noun']} {verb}")
        return text

    def correct_to_simple_past(self, doc, verbs):
        past_keywords = [
            'yesterday',
            'before',
            'last',
            'this morning',
            'ago'
        ]
        verbs = verbs.copy()
        text = doc.text
        past_signal = any(past_word in text for past_word in past_keywords)
        if past_signal:
            for i, (current, prev) in enumerate(verbs):
                # if current is verb to be and the next word is verb continue else replace
                if current['form'][0] == 'Fin' and current['verb'] in self.all_verb_to_be:
                    if self.check_next_if_verb(verbs, i, current):
                        continue

                    if 'noun' in prev.keys():
                        verb_to_be = self.check_to_for(prev, current)
                        if not verb_to_be:
                            verb_to_be = 'was' if prev['number'][0] == 'Sing' else "were"
                    else:
                        verb_to_be = ""
                    text = self.replace(text, current['verb'], verb_to_be)
                #     have,has,had
                elif current['form'][0] == 'Fin' and current['verb'] in self.perfect_aux:
                    if self.check_next_if_verb(verbs, i, current):
                        continue

                    if 'noun' in prev.keys():
                        verb = self.check_to_for(prev, current)
                        if not verb:
                            verb = self.get_past_form(current)
                        text = text.replace(f"{prev['noun']} {current['verb']}",
                                            f"{prev['noun']} {verb}")

                elif current['form'][0] == 'Fin' and current['verb'] == 'will':
                    continue
                # Fin -> with s , Inf -> without s, Part  -> ing | ed
                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    # if prev is verb to be or will
                    # if 'verb' in prev.keys() and (prev['verb'] in self.all_verb_to_be or prev['verb'] == 'will'):
                    #     text = text.replace(f"{prev['verb']} {current['verb']}",
                    #                         self.get_past_form(current))

                    # if prev is perfect_aux or will
                    if 'verb' in prev.keys():
                        if prev['verb'] == 'will':
                            text = text.replace(f"{prev['verb']} {current['verb']}",
                                                self.get_past_form(current))
                        elif prev['verb'] in self.perfect_aux:
                            text = text.replace(f"{prev['verb']} {current['verb']}",
                                                self.get_past_form(current))
                    else:
                        verb = self.check_to_for(prev, current)
                        if not verb:
                            verb = self.get_past_form(current)
                        text = self.replace(text, current['verb'], verb)
        return text

    # here we only convert present cont to past, the other forms are converted to past simple
    def correct_to_past_cont(self, doc, verbs):
        past_keywords = [
            'yesterday',
            'before',  # the day before
            'last',
            'this morning',
            'ago'
        ]
        verbs = verbs.copy()
        text = doc.text
        past_signal = any(past_word in text for past_word in past_keywords)
        if past_signal:
            for i, (current, prev) in enumerate(verbs):
                if current['form'][0] == 'Fin' and current['verb'] in self.all_verb_to_be:
                    # if prev word is noun replace verb to be to suitable one else delete
                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        if 'noun' in prev.keys():
                            verb_to_be = self.check_to_for(prev, current)
                            if not verb_to_be:
                                verb_to_be = 'was' if prev['number'][0] == 'Sing' else "were"
                        else:
                            verb_to_be = ""
                        if c == current and 'verb' in next.keys():
                            text = text.replace(f"{current['verb']} {next['verb']} ",
                                                f"{verb_to_be} {self.get_verb_ing(next)} ")
                            verbs.pop(i + 1)
                elif current['form'][0] == 'Fin' and current['verb'] == 'will':
                    continue
                # has,have,had
                elif current['form'][0] == 'Fin' and current['verb'] in self.perfect_aux:
                    if self.check_next_if_verb(verbs, i, current):
                        continue
                    if 'noun' in prev.keys():
                        verb = self.check_to_for(prev, current)
                        if verb is not None:
                            text = text.replace(f"{prev['noun']} {current['verb']} ", f"{prev['noun']} {verb} ")

                # this to words after to,for
                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    if 'noun' in prev.keys():
                        verb = self.check_to_for(prev, current)
                        if verb is not None:
                            text = text.replace(f"{prev['noun']} {current['verb']} ", f"{prev['noun']} {verb} ")
                        # verb_to_be = 'was' if prev['number'][0] == 'Sing' else "were"
                        # text = self.replace(text, current['verb'], f"{verb_to_be} {current['lemma']}ing")
        return text

    def correct_to_present_cont(self, doc, verbs):
        present_keywords = ['now', 'at the moment', 'today']
        verbs = verbs.copy()
        text = doc.text
        present_signal = any(present_word in text for present_word in present_keywords)

        if present_signal:
            for i, (current, prev) in enumerate(verbs):
                if current['form'][0] == 'Fin' and \
                        (current['verb'] in self.all_verb_to_be or current['verb'] == 'will' or self.perfect_aux):
                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        # if prev word is noun replace verb to suitable verb to be else delete
                        if 'noun' in prev.keys():
                            verb_to_be = self.check_to_for(prev, current)
                            if not verb_to_be:
                                verb_to_be = 'am' if prev['noun'] == 'i' else 'is' if prev['number'][
                                                                                          0] == 'Sing' else "are"
                        else:
                            verb_to_be = ""
                        if c == current and 'verb' in next.keys():
                            text = text.replace(f"{current['verb']} {next['verb']} ",
                                                f"{verb_to_be} {self.get_verb_ing(next)} ")
                            verbs.pop(i + 1)

                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    if 'noun' in prev.keys():
                        verb_to_be = self.check_to_for(prev, current)
                        if not verb_to_be:
                            verb_to_be = 'am' if prev['noun'] == 'i' else 'is' if prev['number'][0] == 'Sing' else "are"
                            text = self.replace(text, current['verb'], f"{verb_to_be} {self.get_verb_ing(current)}")
                        else:
                            text = text.replace(f"{prev['noun']} {current['verb']} ", f"{prev['noun']} {verb_to_be} ")

        return text

    def correct_to_future(self, doc, verbs):
        future_keywords = ['tomorrow', 'next']
        verbs = verbs.copy()
        text = doc.text
        future_signal = any(future_keyword in text for future_keyword in future_keywords)

        if future_signal:
            for i, (current, prev) in enumerate(verbs):
                # if current is verb to be and the next word is verb continue else replace
                if current['form'][0] == 'Fin' and (
                        current['verb'] in self.all_verb_to_be or current['verb'] in self.perfect_aux):
                    if self.check_next_if_verb(verbs, i, current):
                        continue

                    verb = None
                    if 'noun' in prev:
                        verb = self.check_to_for(prev, current)
                    if not verb:
                        verb = f"will {current['lemma']}"
                    text = self.replace(text, current['verb'], verb)
                elif current['form'][0] == 'Fin' and current['verb'] == 'will':
                    continue
                # Fin -> with s , Inf -> without s, Part  -> ing | ed
                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    # if prev is verb to be or will
                    if 'verb' in prev.keys():
                        if self.check_prev_if_verb(prev):
                            text = text.replace(f"{prev['verb']} {current['verb']}",
                                                f"will {current['lemma']}")
                    else:
                        verb = self.check_to_for(prev, current)
                        if not verb:
                            verb = f"will {current['lemma']}"
                        prev_word = prev['noun'] if 'noun' in prev.keys() else prev['verb']
                        text = text.replace(f"{prev_word} {current['verb']}", f"{prev_word} {verb}")
            return text

    def correct_to_present_perfect(self, doc, verbs):
        present_perfect_keywords = ['since', 'until', 'yet', 'already', 'just', 'recently', 'so far', 'ever']
        verbs = verbs.copy()
        text = doc.text
        present_signal = any(present_word in text for present_word in present_perfect_keywords) or re.search(r"for \d+",
                                                                                                             text)
        if present_signal:

            for i, (current, prev) in enumerate(verbs):
                if current['form'][0] == 'Fin' and \
                        (current['verb'] in self.all_verb_to_be or current['verb'] == 'will' or current['verb'] in self.perfect_aux):
                    if i < len(verbs) - 1:
                        next, c = verbs[i + 1]
                        # if prev word is noun replace verb to suitable aux else delete
                        if 'noun' in prev.keys():
                            verb = self.check_to_for(prev, current)
                            if not verb:
                                verb = 'have' if prev['noun'] == 'i' \
                                                 or prev['number'][0] == 'Plur' else "has"
                        else:
                            verb = ""
                        if c == current and 'verb' in next.keys():
                            text = text.replace(f"{current['verb']} {next['verb']} ",
                                                f"{verb} {self.get_past_participle(next)} ")
                            verbs.pop(i + 1)

                elif current['form'][0] in ('Fin', 'Inf', 'Part'):
                    if 'noun' in prev.keys():
                        verb = self.check_to_for(prev, current)
                        if not verb:
                            verb = 'have' if prev['noun'] == 'i' \
                                             or prev['number'][0] == 'Plur' else "has"
                            text = self.replace(text, current['verb'], f"{verb} {self.get_past_participle(current)}")
                        else:

                            text = text.replace(f"{prev['noun']} {current['verb']} ", f"{prev['noun']} {verb} ")

        return text


c = CorrectVerb()

for example in examples:
    correct = c.correct(example)
    print()
