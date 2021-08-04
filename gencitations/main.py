import argparse
import itertools as it
import re
import sys

import diskcache as dc
import requests


cache = dc.Cache()


def parse_orca(text):
    kwds_re = re.compile(r"\|  \d> !(.+)")
    kw_lines = kwds_re.findall(text)
    keywords = list(it.chain(*[kw_line.strip().split() for kw_line in kw_lines]))
    return keywords


def normalize_orca_keywords(keywords):
    keywords += ["orca"]
    keywords = [kw.strip().lower() for kw in keywords]
    keywords = set(keywords)  # Avoid duplicates
    return keywords


def clean_keyword(kw):
    keep_re = re.compile("[\W]")
    kw_clean = keep_re.sub("", kw)
    return kw_clean


def dois_for_orca_kw(kw):
    DOIS = {
        "orca": ["10.1063/5.0004608"],
        "ri-mp2": ["10.1080/00268976.2013.824624"],
        "6-31g*" : ["10.1063/1.1674902", "10.1007/bf00533485", "10.1063/1.1677527"],
    }
    try:
        dois = DOIS[kw]
    except KeyError:
        print(f"No doi(s) for keyword '{kw}'")
        dois = []
    return dois


@cache.memoize()
def bibtex_from_doi(doi):
    tpl = "https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
    rendered = tpl.format(doi=doi)
    try:
        resp = requests.get(rendered)
    except requests.exceptions.RequestException as err:
        print(err)
        resp = None
    return resp.text


def prepend_bibtex_name(bibtex, prepend_name):
    name_re = re.compile(r"(\@[a-zA-Z]+\{)(.+?)(,.+)", re.DOTALL)
    sub = r"\g<1>{}\g<2>\g<3>".format(prepend_name)
    bibtex_ = name_re.sub(sub, bibtex)
    return bibtex_


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("orca_log")
    parser.add_argument("--bib_out", default="bibliography.bib")
    parser.add_argument("--cache", )

    return parser.parse_args(args)


def run():
    args = parse_args(sys.argv[1:])

    with open(args.orca_log) as handle:
        text = handle.read()

    keywords = parse_orca(text)
    keywords = normalize_orca_keywords(keywords)

    all_bibtexs = list()
    for kw in keywords:
        dois = dois_for_orca_kw(kw)
        if not dois:
            continue
        # Prepend keyword
        bibtexs = [
            # f"%{kw}\n" + bibtex
            bibtex
            for doi in dois
            if (bibtex := bibtex_from_doi(doi)) is not None
        ]
        if not bibtexs:
            continue
        kw_clean = clean_keyword(kw)
        for i, bibtex in enumerate(bibtexs):
            prepend_name = f"{kw_clean}_{i}_"
            bibtex = prepend_bibtex_name(bibtex, prepend_name)
            print(bibtex)
            print()
            all_bibtexs.append(bibtex)

    with open(args.bib_out, "w") as handle:
        handle.write("\n\n".join(all_bibtexs))
    print(f"Wrote bibliography to '{args.bib_out}'")


if __name__ == "__main__":
    run()
