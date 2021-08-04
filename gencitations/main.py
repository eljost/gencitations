import argparse
import itertools as it
import os
from pathlib import Path
import re
import sys

import diskcache as dc
import requests
import yaml


cache = dc.Cache(directory=".")


def parse_orca(text):
    """Return keywords from ORCA logfile."""
    kwds_re = re.compile(r"\|  \d> !(.+)")
    kw_lines = kwds_re.findall(text)
    keywords = list(it.chain(*[kw_line.strip().split() for kw_line in kw_lines]))
    return keywords


def normalize_orca_keywords(keywords):
    """Remove leading/trailing whitespace and convert to lowercase."""
    keywords += ["orca"]
    keywords = [kw.strip().lower() for kw in keywords]
    keywords = set(keywords)  # Avoid duplicates
    return keywords


def clean_keyword(kw):
    """Remove special characters."""
    repls = (("+", "plus"), ("*", "star"), ("-", "_"))
    for ptrn, sub in repls:
        kw = kw.replace(ptrn, sub)
    keep_re = re.compile(r"[\W]")
    kw_clean = keep_re.sub("", kw)
    return kw_clean


def dois_for_orca_kw(kw, dois_dict):
    """Get document object identifiers for given keyword."""
    try:
        dois = dois_dict[kw]
    except KeyError:
        print(f"No doi(s) for keyword '{kw}'")
        dois = []
    return dois


@cache.memoize()
def bibtex_from_doi(doi):
    """Fetch bibtex entry for given DOI from Crossref API. """
    tpl = "https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
    rendered = tpl.format(doi=doi)
    try:
        resp = requests.get(rendered)
        print(f"Performed API lookup at '{rendered}'")
    except requests.exceptions.RequestException as err:
        print(err)
        resp = None
    return resp.text


def prepend_bibtex_name(bibtex, prepend_name):
    """Fix bibtex name."""
    name_re = re.compile(r"(\@[a-zA-Z]+\{)(.+?)(,.+)", re.DOTALL)
    sub = r"\g<1>{}\g<2>\g<3>".format(prepend_name)
    bibtex_ = name_re.sub(sub, bibtex)
    return bibtex_


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("orca_log")
    parser.add_argument("--bib_out", default="bibliography.bib")
    parser.add_argument("--cache", )
    parser.add_argument("--dois", default=None, type=str)

    return parser.parse_args(args)


def run():
    args = parse_args(sys.argv[1:])

    with open(args.orca_log) as handle:
        text = handle.read()

    this_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    if args.dois is None:
        dois_fn = this_dir / "dois.yaml"
    else:
        dois_fn = args.dois
    with open(dois_fn) as handle:
        doi_dict = yaml.load(handle.read(), Loader=yaml.SafeLoader)
    print(f"Loaded DOIs for {len(doi_dict.keys())} keywords from '{dois_fn}'.")

    keywords = parse_orca(text)
    keywords = normalize_orca_keywords(keywords)

    all_bibtexs = list()
    ignored_kws = list()
    for kw in keywords:
        dois = dois_for_orca_kw(kw, doi_dict)
        bibtexs = [
            bibtex
            for doi in dois
            if (bibtex := bibtex_from_doi(doi)) is not None
        ]
        if not bibtexs:
            ignored_kws.append(kw)
            continue
        kw_clean = clean_keyword(kw)
        for i, bibtex in enumerate(bibtexs):
            prepend_name = f"{kw_clean}_{i}_"
            bibtex = prepend_bibtex_name(bibtex, prepend_name)
            # Also prepend keyword as comment
            bibtex = f"%{kw}\n" + bibtex
            print(bibtex)
            print()
            all_bibtexs.append(bibtex)

    with open(args.bib_out, "w") as handle:
        handle.write("\n\n".join(all_bibtexs))

    print()
    print(f"Ignored keywords: {', '.join(ignored_kws)}")
    print(f"Wrote bibliography to '{args.bib_out}'")


if __name__ == "__main__":
    run()
