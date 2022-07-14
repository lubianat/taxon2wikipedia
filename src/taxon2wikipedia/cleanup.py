from pathlib import Path
import collections
import re
from typing import OrderedDict
import json

HERE = Path(__file__).parent.resolve()
DICTS = HERE.parent.joinpath("dicts")


def main():
    wikipage_path = HERE.parent.parent.joinpath("wikipage.txt")
    wikipage = wikipage_path.read_text()
    wikipage = merge_equal_refs(wikipage)
    wikipage_path.write_text(wikipage)


DESCRIPTION_DICT = OrderedDict(
    {
        ". Folhas ": ". Ela tem [[folhas]] ",
        ". Flores ": ". Ela tem [[flores]] ",
        ". Pedicelo ": ". Tem [[pedicelo]] ",
        ". Labelo ": ". Possui [[labelo]] ",
        ". Pecíolo ": ". Possui pecíolo ",
    }
)

BOTANICAL_DICT = json.loads(DICTS.joinpath("botanical_terms_wiki_pt.json").read_text())

REPLACE_DICT = json.loads(DICTS.joinpath("replace_dict_pt.json").read_text())

# Cannot be factored out into json due to different quote styling
RESUB_DICT = {
    "compr\n": "de comprimento\n",
    "<span(.|\n)*?>": "",
    "<p class(.|\n)*?>": "",
    "</p>": "",
    "</span>": "",
    "</i>": "",
    "<i>": "",
    "</b>": "",
    "<b>": "",
    "<span>": "",
    "<w:.*?>": "",
    "</w.*?>": "",
    "</st1:.*?>": "",
    "<st1:.*?>": "",
    "<o:p></o:p>": "",
    "&nbsp;": " ",
    " ca. ": " com cerca de ",
    '<p style="margin-bottom: 0px; font-size: 11px; line-height: normal; font-family: Times; color: rgb\(47, 42, 43\);">': "",
    '<i style="font-size: 13px;">': "",
}


def fix_description(wikipage):
    for key, value in REPLACE_DICT.items():
        wikipage = wikipage.replace(key, value)

    for key, value in RESUB_DICT.items():
        wikipage = re.sub(key, value, wikipage)

    for key, value in DESCRIPTION_DICT.items():
        wikipage = re.sub(key, value, wikipage, 1)

    for key, value in BOTANICAL_DICT.items():
        wikipage = re.sub(f" {key} ", f" {value} ", wikipage, 1)
        wikipage = re.sub(f" {key}s ", f" {value}s ", wikipage, 1)
        wikipage = re.sub(f" {key.capitalize} ", f" {value} ", wikipage, 1)
        wikipage = re.sub(f" {key.capitalize}s ", f" {value}s ", wikipage, 1)

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
