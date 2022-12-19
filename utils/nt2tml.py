"""Converts NarrativeTime annotations into TimeML format.

Usage example:
    python narrative_time/nt2tml.py \
        --input_file corpus/timebank/nt_format/tbd_a1_tml.jsonl \
        --output_dir corpus/timeml_converted/a1
"""

import os
import traceback
import argparse

from loguru import logger
from tqdm import tqdm
from bs4 import BeautifulSoup, NavigableString

from narrative_time import event_relations
from narrative_time import conversion_utils as utils


# optional fields for text2xml:
# (required fields are explicitly checked in the script)
TIMEX3_FIELDS = ["type", "value", "temporalFunction", "functionInDocument", "beginPoint", "endPoint", "quant", "freq", "value", "valueFromFunction", "mod", "anchorTimeID", "comment"]
EVENT_FIELDS = ["class", "comment"]
MAKEINSTANCE_FIELDS = ["signalID", "pos", "tense", "aspect", "cardinality", "polarity", "modality", "comment"]

# optionally, we add narrative time tags to events
# we add nt_ to distinguish them from the original event fields, like timex "type"
NT_FIELDS_DICT = {
    "event_type": "nt_type",
    "time": "nt_time",
    "branch": "nt_branch",
    "factuality": "nt_factuality",
}


def text2xml(text, events_and_timexes, add_narrative_time_info=False):
    """
    Wrapping a text with NarrativeTime event and timex annotations into TimeML-
    style XML formatted text + a list of "makeinstance" event tags. Assumes
    the NT span annotations are non-overlapping (otherwise XML will be invalid)

    Args:
        text (str): the annotated text
        events_and_timexes (dict): the events metadata (output of get_events_and_timexes)
        add_narrative_time_info (bool): whether to add NarrativeTime event and timex metadata to the XML,
            useful for debugging and readability of the XML
    Returns:
        (object): Beautiful Soup XML object with the text (including TIMEX3 and EVENT tags) and MAKEINSTANCE tags
    """
    tokenidx2event = {e["span"][0]: {**e, "eiid": k} for k, e in events_and_timexes.items()}

    header = '<?xml version="1.0" encoding="utf-8"?><TimeML>\n</TimeML>'
    soup = BeautifulSoup(header, features="xml")
    soup.TimeML.string = ""
    instances = []

    tokens = text.split(" ")
    for instance in range(len(tokens)):
        if instance not in tokenidx2event:
            soup.TimeML.append(NavigableString(f"{tokens[instance]} "))
            continue

        event = tokenidx2event[instance]
        l, r = event["span"]
        span_text = " ".join(tokens[l:r + 1])

        if event["is_timex"]:
            # is timex
            # we have key collition for "type" between timex metadata and NarrativeTime annotation
            # this is why this script renames the NarrativeTime annotation to "event_type"
            to_pass = {k: event[k] for k in TIMEX3_FIELDS if k in event and k != "type"}
            if add_narrative_time_info:
                to_pass.update({nt_k: event[k] for k, nt_k in NT_FIELDS_DICT.items()})
            assert event["eiid"].startswith("t")
            tag = soup.new_tag("TIMEX3", tid=event["eiid"], **to_pass)

            tag.string = span_text
            soup.TimeML.append(tag)
            continue

        # is event
        to_pass = {k: event[k] for k in EVENT_FIELDS if k in event}
        if add_narrative_time_info:
            to_pass.update({nt_k: event[k] for k, nt_k in NT_FIELDS_DICT.items()})

        tag = soup.new_tag("EVENT", eid=event["eid"], **to_pass)
        tag.string = span_text
        soup.TimeML.append(tag)

        to_pass_instance = {k: event[k] for k in MAKEINSTANCE_FIELDS if k in event}
        assert not event["eiid"].startswith("t")
        instance_tag = soup.new_tag("MAKEINSTANCE", eiid=event["eiid"], eventID=event["eid"], **to_pass_instance)
        instances.append(instance_tag)

    soup.smooth()
    for instance in instances:
        soup.TimeML.append(instance)

    return soup


def get_factuality_tags(events_and_timexes, soup):
    """Converting factuality annotation to FactBank format

    Args:
        soup (object): BS4 xml object (output of text2xml), only needed to create new tags, not modified in place
        events_and_timexes (dict): events metadata dictionary (output of get_events_and_timexes)
        invisible_events (list): the eiids of events that were not visible to the annotator
        event_coref (list of lists): individual coreference chains are represented by lists of eiids in the chain

    Returns:
        list: list of  BS4 tags with FACT_VALUE
    """

    codes = {"": "CT+", "-": "CT-", "m": "PS+", "m-": "PS-"}
    idx = 1
    tags = []

    for eiid, event in events_and_timexes.items():
        if event["is_timex"]: continue
        factuality = codes[event["factuality"]]
        tag = soup.new_tag("FACT_VALUE", fvid=idx, eiid=eiid, value=factuality)
        tags.append(tag)
        idx += 1

    return tags


def get_tlinks(events_and_timexes, soup):
    """Converting tlink annotation to FactBank format

    Args:
        soup (object): BS4 xml object (output of text2xml), only needed to create new tags, not modified in place
        events_and_timexes (dict): the events metadata (output of get_events_and_timexes)
            here's what it looks like:
            {
                't0': {'span': [5, 6], 'is_timex': True,
                       'type': '[B]', 'time': '1', 'relto': '', 'factuality': ''},
                'ei0': {'span': [94, 94], 'is_timex': False, 'eid': '0',
                        'type': '[U}', 'time': '-0.1', 'relto': '', 'factuality': ''},
                ...
            }

    Returns:
        list: list of  BS4 tags with TLINK
    """
    lid = 1
    tlinks = []
    for eeid1, event1 in events_and_timexes.items():
        for eeid2, event2 in events_and_timexes.items():
            if eeid1 == eeid2: continue

            key1 = "timeID" if event1["is_timex"] else "eventInstanceID"
            key2 = "relatedToTime" if event2["is_timex"] else "relatedToEventInstance"
            kwargs = {key1: eeid1, key2: eeid2}

            if event1["branch"] == event2["branch"]:
                relation = event_relations.get_event_relation(event1, event2)

                tlink = soup.new_tag("TLINK", relType=relation, lid=lid, **kwargs)
                tlinks.append(tlink)
                lid += 1
                continue
            
            # different branches
            relation = event_relations.get_event_relation_separate_branches(event1, event2)

            tlink = soup.new_tag("TLINK", relType=relation, lid=lid, comment="different NT-branches", **kwargs)
            tlinks.append(tlink)
            lid += 1

    return tlinks


def convert_to_timeml(annotation, add_narrative_time_info, corpus_offset=0):
    # convert NarrativeTime format to a json of the following format:
    # {'t0': {'span': [5, 6], 'is_timex': True, 'type': '[B]', 'time': '1', 'relto': '', 'factuality': ''},
    # 'ei0': {'span': [94, 94], 'is_timex': False, 'eid': '0', 'type': '[U}', 'time': '-0.1', 'relto': '', 'factuality': ''},
    events_and_timexes = utils.get_events_and_timexes(annotation, corpus_offset=corpus_offset)

    # Step 2: make XML header with "TEXT" and "MAKEINSTANCE"
    soup = text2xml(
        annotation["text"],
        events_and_timexes,
        add_narrative_time_info=add_narrative_time_info,
    )

    # Step 3: add tags
    factuality_tags = get_factuality_tags(events_and_timexes, soup)
    tlinks = get_tlinks(events_and_timexes, soup)

    # Step 4: add tags to the soup
    for tag in factuality_tags + tlinks:
        soup.TimeML.append(tag)

    return soup


def parse_nt_json(input_file, output_dir, use_global_eiid=True, add_narrative_time_info=False, verbocity=1):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Can't find {input_file}")
    os.makedirs(output_dir, exist_ok=True)

    annotations = utils.get_annotations(input_file)

    n_errors = 0
    n_files = len(annotations)
    error_summary = ""
    corpus_offset = 0

    for annotation in tqdm(annotations, desc="Converting to TimeML", disable=verbocity==0):
        try:
            # conversion happens here
            timeml_soup = convert_to_timeml(annotation, add_narrative_time_info=add_narrative_time_info, corpus_offset=corpus_offset)
            soup_str = utils.prettify_soup(timeml_soup)
            if use_global_eiid:
                corpus_offset += len(annotation["events"])
        except Exception as e:
            n_errors += 1
            error_summary += f"{annotation['id']}: {e}\n"
            if verbocity > 0:
                logger.error(f"Error converting {annotation['id']}")
                traceback.print_exc()
            continue

        # save to file
        output_file = os.path.join(output_dir, f"{annotation['id']}.tml")
        with open(output_file, "w") as f:
            f.write(soup_str)

    if verbocity > 0:
        logger.info(f"Converted {n_files - n_errors} out of {n_files} files")

    if n_errors > 0:
        # required for the tests to work correctly and fail when the script it not working
        raise ValueError(f"Conversion finished with {n_errors} errors out of {n_files} files.\n\n" + error_summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True, help="jsonl data file in NarrativeTime format")
    parser.add_argument("--output_dir", required=True, help="folder for saving xml files in TimeML format")
    parser.add_argument("--verbocity", default=1, help="0 - silent, 1 - print final results, 2 - print all")
    parser.add_argument("--add_narrative_time_info", default=False, action="store_true", help="add NarrativeTime tags to the output xml file. Useful for debugging and readability.")
    parser.add_argument("--do_not_use_global_eiid", default=False, action="store_true", help="Always generate eiids starting from 0. Useful for testing.")
    args = parser.parse_args()

    logger.info(f"Starting script with args {vars(args)}")
    parse_nt_json(
        input_file=args.input_file,
        output_dir=args.output_dir,
        verbocity=args.verbocity,
        use_global_eiid=not args.do_not_use_global_eiid,
        add_narrative_time_info=args.add_narrative_time_info,
    )
