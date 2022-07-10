from pathlib import Path
import collections
import re
from typing import OrderedDict

HERE = Path(__file__).parent.resolve()


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

BASE_DESCRIPTION_DICT = OrderedDict(
    {
        "corola": "[[corola]]",
        "pecíolo": "[[Pecíolo (botânica)|pecíolo]]",
        "pedicelo": "[[pedicelo]]",
        "tricoma": "[[tricoma]]",
        "hipanto": "[[hipanto]]",
        "bractéola": "[[bractéola]]",
        "pétala": "[[pétala]]",
        "estípula": "[[estípula]]",
        "drupa": "[[drupa]]",
        "sépala": "[[sépala]]",
        "antera": "[[antera]]",
        "bráctea": "[[bráctea]]",
        "subarbusto": "[[subarbusto]]",
        "lâmina foliar": "[[lâmina foliar]]",
        "cálice": "[[Cálice (botânica)|cálice]]",
        "filídio": "[[filídio]]",
        "rizóide": "[[rizóide]]",
        "anfigastro": "[[anfigastro]]",
        "anterídeo": "[[anterídeo]]",
        "pseudobulbo": "[[pseudobulbo]]",
        "dicásio": "[[dicásio]]",
    }
)


def fix_description(wikipage):
    wikipage = wikipage.replace("compr.", "de comprimento")
    wikipage = wikipage.replace(" m ", " metros ")
    wikipage = wikipage.replace(" cm ", " centímetros ")
    wikipage = wikipage.replace(" mm ", " milímetros ")
    wikipage = wikipage.replace("alt.", "de altura")
    wikipage = re.sub("<span(.|\n)*?>", "", wikipage)
    wikipage = re.sub("<p class(.|\n)*?>", "", wikipage)
    wikipage = re.sub("</p>", "", wikipage)
    wikipage = re.sub("</span>", "", wikipage)
    wikipage = re.sub("</i>", "", wikipage)
    wikipage = re.sub("<i>", "", wikipage)
    wikipage = re.sub("<span>", "", wikipage)
    wikipage = re.sub("<o:p></o:p>", "", wikipage)
    wikipage = re.sub("&nbsp;", " ", wikipage)
    wikipage = re.sub(" ca. ", " com cerca de ", wikipage)

    wikipage = re.sub(
        '<p style="margin-bottom: 0px; font-size: 11px; line-height: normal; font-family: Times; color: rgb\(47, 42, 43\);">',
        "",
        wikipage,
    )

    for key, value in DESCRIPTION_DICT.items():
        wikipage = re.sub(key, value, wikipage, 1)

    for key, value in BASE_DESCRIPTION_DICT.items():
        wikipage = re.sub(f" {key} ", f" {value} ", wikipage, 1)
        wikipage = re.sub(f" {key}s ", f" {value}s ", wikipage, 1)
        wikipage = re.sub(f" {key.capitalize} ", f" {value} ", wikipage, 1)
        wikipage = re.sub(f" {key.capitalize}s ", f" {value}s ", wikipage, 1)

    return wikipage


def merge_equal_refs(wikipage):
    results = re.findall(f"(<ref>.*?</ref>)", wikipage)
    repeated_refs = [item for item, count in collections.Counter(results).items() if count > 1]
    print(repeated_refs)

    for i, repeated_ref in enumerate(repeated_refs):
        parts = wikipage.partition(repeated_ref)  # returns a tuple
        print(parts[1])
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
