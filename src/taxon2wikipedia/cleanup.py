import collections
import json
import re
from pathlib import Path
from typing import OrderedDict

HERE = Path(__file__).parent.resolve()
DICTS = HERE.parent.joinpath("dicts")


def main():
    wikipage_path = HERE.parent.parent.joinpath("wikipage.txt")
    wikipage = wikipage_path.read_text()
    wikipage = merge_equal_refs(wikipage)
    wikipage_path.write_text(wikipage)


DESCRIPTION_DICT = json.loads(DICTS.joinpath("phrase_start_dict.json").read_text())
BOTANICAL_DICT = json.loads(DICTS.joinpath("botanical_terms_wiki_pt.json").read_text())
REPLACE_DICT = json.loads(DICTS.joinpath("replace_dict_pt.json").read_text())
TABLE_REPLACE_DICT = json.loads(
    DICTS.joinpath("description_table_replace_dict_pt.json").read_text()
)

REPLACE_DICT.update(TABLE_REPLACE_DICT)
# Cannot be factored out into json due to different quote styling
RESUB_DICT = {
    "compr\n": "de comprimento\n",
    "<span(.|\n)*?>": "",
    "<span(.|\n)*?>": "",
    "<p class(.|\n)*?>": "",
    "</p>": "",
    "</span>": "",
    "</i.*?>": "",
    "<i.*?>": "",
    "</b>": "",
    "<br>": "\n",
    "<b(.|\n)*?>": "",
    "<!--(.|\n)*?-->": "",
    "<span>": "",
    "<w:(.|\n)*?>": "",
    "<font(.|\n)*?>": "",
    "</font(.|\n)*?>": "",
    "<xml>(.|\n)*?</xml>": "",
    "</w.*?>": "",
    "<div.*?>": "",
    "</div*?>": "",
    "</st1:.*?>": "",
    "<st1:.*?>": "",
    "<o:p></o:p>": "",
    "&nbsp;": " ",
    " ca. ": " com cerca de ",
    '<p style="margin-bottom: 0px; font-size: 11px; line-height: normal; font-family: Times; color: rgb\(47, 42, 43\);">': "",
    '<i style="font-size: 13px;">': "",
    "(?<!de) ([1-9]–)": " de \\1",
}


def fix_description(wikipage):
    """
    Substitutes parts of description to comply with Wikimedia guidelines.

    """
    for key, value in REPLACE_DICT.items():
        wikipage = re.sub(f"([^a-zA-ZÀ-ÿ]+){key}([^a-zA-sZÀ-ÿ]+)", f"\\1 {value}\\2", wikipage)
        wikipage = wikipage.replace("  ", " ")
        wikipage = wikipage.replace("' ", "'")

    for key, value in RESUB_DICT.items():
        wikipage = re.sub(key, value, wikipage)

    for key, value in DESCRIPTION_DICT.items():
        wikipage = re.sub(key, value, wikipage, 1)

    for key, value in BOTANICAL_DICT.items():
        wikipage = re.sub(f"([^a-zA-Z\[]+){key}([^a-zA-Z]+)", f"\\1{value}\\2", wikipage, 1)
        wikipage = re.sub(f"([^a-zA-Z\[]+){key}s([^a-zA-Z]+)", f"\\1{value}s\\2", wikipage, 1)
        wikipage = re.sub(f" {key.capitalize} ", f" {value} ", wikipage, 1)
        wikipage = re.sub(f" {key.capitalize}s ", f" {value}s ", wikipage, 1)

    wikipage = re.sub(r"(?!de) ([0-9|\.]+)–([0-9|\.]+)", " de \\1 a \\2", wikipage)
    wikipage = re.sub(r"\( (.*?) \)", "(\\1)", wikipage)
    return wikipage


def merge_equal_refs(wikipage):
    results = re.findall(f"(<ref>.*?</ref>)", wikipage)
    repeated_refs = [item for item, count in collections.Counter(results).items() if count > 1]

    for i, repeated_ref in enumerate(repeated_refs):
        parts = wikipage.partition(repeated_ref)  # returns a tuple
        print("========")
        wikipage = (
            parts[0]
            + re.sub(
                re.escape(repeated_ref),
                f'<ref name=":ref_{str(i)}"> {repeated_ref.replace("<ref>", "")}',
                parts[1],
            )
            + re.sub(
                re.escape(repeated_ref),
                f'<ref name=":ref_{str(i)}"/>',
                parts[2],
            )
        )
    return wikipage


if __name__ == "__main__":
    main()
