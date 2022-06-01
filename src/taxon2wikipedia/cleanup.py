from pathlib import Path
import collections
import re

HERE = Path(__file__).parent.resolve()


def main():
    wikipage_path = HERE.parent.parent.joinpath("wikipage.txt")

    wikipage = wikipage_path.read_text()
    wikipage = merge_equal_refs(wikipage)

    wikipage_path.write_text(wikipage)


def fix_description(wikipage):
  wikipage = wikipage.replace("compr.", "de comprimento")
  wikipage = re.sub('<span.*?>','',wikipage)
  return wikipage



def merge_equal_refs(wikipage):
    results = re.findall(f"(<ref>.*?</ref>)", wikipage)
    repeated_refs = [
        item for item, count in collections.Counter(results).items() if count > 1
    ]
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
