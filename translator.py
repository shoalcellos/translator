import requests
from bs4 import BeautifulSoup
import sys

LANGUAGES = {
    1: "Arabic",
    2: "German",
    3: "English",
    4: "Spanish",
    5: "French",
    6: "Hebrew",
    7: "Japanese",
    8: "Dutch",
    9: "Polish",
    10: "Portuguese",
    11: "Romanian",
    12: "Russian",
    13: "Turkish"
}


# define Python user-defined exceptions
class TranslatorError(Exception):
    """Base class for other exceptions"""


class WordError(TranslatorError):

    def __init__(self, message):
        self.message = message


class InternetError(TranslatorError):

    def __init__(self, message):
        self.message = message


def greet():
    print("Hello, you're welcome to the translator.\nTranslator supports: ")

    print("\n".join([f"{index}. {language}" for index, language in LANGUAGES.items()]))

    lang_from = int(input("Type the number of your language:\n"))
    lang_to = int(input("Type the number of a language you want to translate to or '0' to translate to all"
                        " languages:\n"))

    word_to_translate = input("Type the word you want to translate:\n")

    return lang_from, lang_to, word_to_translate


def get_url(lang_from, lang_to, _word):
    translation_dir = f'{lang_from.lower()}-{lang_to.lower()}'
    return f"https://context.reverso.net/translation/{translation_dir}/{_word}"


def get_page(url):
    # define the headers for the request
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/80.0.3987.132 Safari/537.36"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content


def parse_page(body):
    # Parsing the content of the response
    soup = BeautifulSoup(body, 'html.parser')

    # Select translated words

    words = [x.text.strip() for x in soup.select("#translations-content > .translation")]

    # Select usage examples
    examples = [x.text.strip() for x in soup.select("#examples-content span.text")]

    source_sentences = examples[0::2]
    target_sentences = examples[1::2]
    sentences_together = [":\n".join(x) for x in zip(source_sentences, target_sentences)]

    return words, sentences_together


def create_string(words, sentences_together, to_language, multiple_languages=False):
    if multiple_languages:
        out_string = f"{to_language} Translations:\n" \
                     f"{words[0]}" \
                     "\n\n" \
                     f"{to_language} Examples:\n" \
                     f"{sentences_together[0]}"
    else:
        out_string = f"{to_language} Translations:\n" + \
                     "\n".join(words[:5]) + \
                     "\n\n" + \
                     f"{to_language} Examples:\n" + \
                     "\n\n".join(sentences_together[:5])
    return out_string


def get_translations(lang_from, lang_to, _word, language_dict):
    if lang_to == 0:
        urls = {x: get_url(language_dict[lang_from],
                           language_dict[x], _word) for x in language_dict.keys() if x != lang_from}
    else:
        urls = {lang_to: get_url(language_dict[lang_from], language_dict[lang_to], _word)}

    output = []

    for to, trans_url in urls.items():
        try:
            page = get_page(trans_url)
        except (requests.ConnectionError, requests.ConnectTimeout,
                requests.ReadTimeout, requests.Timeout):
            raise InternetError("Something wrong with your internet connection")
        except requests.HTTPError:
            raise WordError(f"Sorry, unable to find {_word}")
        if page:
            words, examples = parse_page(page)
            output.append(create_string(
                words, examples, language_dict[to], multiple_languages=len(urls) > 1
            ))
    return "\n\n\n".join(output)


def save_output(string, filename):
    with open(filename, "w") as output_file:
        output_file.write(string)


if __name__ == "__main__":
    arg = sys.argv[1:]
    if arg:
        word = arg[2]
        if arg[0].capitalize() not in LANGUAGES.values():
            print(f"Sorry, the program doesn't support {arg[0]}")
        elif arg[1].capitalize() not in LANGUAGES.values() and arg[1] != "all":
            print(f"Sorry, the program doesn't support {arg[1]}")
        else:
            for key, value in LANGUAGES.items():
                if value.lower() == arg[0]:
                    source_language = key
                if value.lower() == arg[1]:
                    destination_language = key
            if arg[1] == "all":
                destination_language = 0
            try:
                print(get_translations(source_language, destination_language, word, LANGUAGES))
            except (InternetError, WordError) as e:
                print(e.message)

    else:
        source_language, destination_language, word = greet()
        translations = get_translations(source_language, destination_language, word, LANGUAGES)
        if destination_language == 0:
            save_output(translations, f"{word}.txt")
        print(translations)
