from duckling import DucklingWrapper, Language
from pattern.es import parse, split, conjugate, PRESENT, IMPERATIVE, SG
from nltk.tokenize.toktok import ToktokTokenizer
from typing import List, Generator, Any, Tuple
import unicodedata
import requests
import string
import re
import os

PRON_REFL = ["me", "te", "se", "nos", "os"]
PRON_OBJ = ["lo", "los", "la", "las"]
ENCLITIC_PAT = re.compile(
    f".*(?={'|'.join(PRON_REFL)})(?={'|'.join(PRON_OBJ)})?")
DUCK = DucklingWrapper(language=Language.SPANISH, maximum_heap_size='512m')


def tokenize(s: str):
    return ToktokTokenizer().tokenize(s)


def untokenize(tokens):
    return ("".join([
        " " + token if not (token.startswith("'")
                            or tokens[i - 1] in ['¿', '¡'] or token == "...")
        and token not in string.punctuation else token
        for i, token in enumerate(tokens)
    ]).strip())


def normalize(string: str):
    res = unicodedata.normalize('NFKD', string).encode(
        'ascii', 'ignore').decode('utf-8')
    return res


def parse_date(sent: str):
    if sent is None:
        return None
    ans = DUCK.parse_time(sent)
    precedence = ["year", "month", "day", "hour", "minute", "second"]

    if len(ans) > 0:
        text = ans[0]["text"]
        val = ans[0]["value"]["value"]
        if "grain" in ans[0]["value"]:
            if normalize(text.lower()) not in [
                    "manana", "pasado manana", "ayer", "hoy"
            ]:
                precision = precedence[
                    precedence.index(ans[0]["value"]["grain"]) - 1]
            else:
                precision = precedence[precedence.index(
                    ans[0]["value"]["grain"])]
        else:
            precision = None

        if "to" in val:
            return {"text": text, "value": val["to"], "precision": precision}
        else:
            return {"text": text, "value": val, "precision": precision}
    else:
        return None


def is_imperative(word: str):
    base = ENCLITIC_PAT.match(word)
    if base:
        txt = base.group()
        txt = normalize(txt)
        ans = parse(txt, lemmata=True).split('/')
        return True, '/'.join([word] + ans[1:])
    return False, None


def syntax_analyze(sent: str) -> Tuple[List, str]:
    parsed_list = []
    command = None
    if sent is not None:
        parsed = parse(sent, lemmata=True)
        parsed_list = parsed.split(" ")
        for s in split(parsed)[0]:
            if s.index == 0 and s.type != "VB":
                flag, fixed = is_imperative(str(s))
                if flag:
                    parsed_list[s.index] = fixed
                    command = fixed.split("/")[-1]
            if s.index == 0 and s.type == "VB":
                if conjugate(
                        str(s), PRESENT, 2, SG,
                        mood=IMPERATIVE) == str(s).lower():
                    command = str(s).lower()
    if command is None:
        command = "conversar"
    return parsed_list, command


def preprocess(raw_data):
    if raw_data is None:
        return None
    # Remove all non-ascii characters
    res = normalize(raw_data)

    # tokenize
    tokens = tokenize(res)

    # Remove all non-alphanumerical tokens and lowercase them
    tokens = [word.lower() for word in tokens if word.isalnum()]

    # Put tokens together
    res = untokenize(tokens)
    return res


def process(raw_data):
    syntax, command, date, task = [None, None, None, None]

    if raw_data is not None:
        syntax, command = syntax_analyze(raw_data)
        date = parse_date(raw_data)
        try:
            task = raw_data.replace("" if date is None else date["text"], "")
            task = task.split(" ", 1)[1] if command != "conversar" else task
        except Exception:
            pass

    res = {
        "text": raw_data,
        "attr": {
            "datetime": date,
            "command": command,
            "syntax": syntax,
            "task": task
        }
    }
    return res
