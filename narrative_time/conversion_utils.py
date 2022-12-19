import json
from copy import deepcopy
from typing import List, Dict
from loguru import logger


TYPE_TO_NAME = ["[B]", "[C]", "{U}", "[U}", "{U]", "[R>", "<R]"]
NAME_TO_TYPE = {name: idx for idx, name in enumerate(TYPE_TO_NAME)}
ADD_DEBUG_INFO = False


def get_annotations(path, as_dict=False):
    data = []
    data_dict = {}

    with open(path) as f:
        for line in f:
            document = json.loads(line)

            # we rename "type" to "event_type" to avoid collision
            # with TIMEX3 "type" from the timebank metadata
            event_order = {}
            for idx, event in document["event_order"].items():
                event["event_type"] = event.pop("type")
                event_order[idx] = event

            document["event_order"] = event_order
            data.append(document)
            data_dict[document["id"]] = document

    if as_dict:
        return data_dict
    return data


def prettify_soup(soup):
    txt = str(soup)
    txt = txt.replace("\n", "\n\n")
    txt = txt.replace("<TimeML>", "<TimeML>\n\n")
    txt = txt.replace("</TimeML>", "\n\n</TimeML>\n\n")
    txt = txt.replace("<MAKEINSTANCE ", "\n<MAKEINSTANCE ")
    txt = txt.replace("<FACT_VALUE ", "\n<FACT_VALUE ")
    txt = txt.replace("<TLINK ", "\n<TLINK ")
    txt = txt.replace("<TEXT>", "\n<TEXT>")
    txt = txt.replace("</TEXT>", "</TEXT>\n")
    return txt


def get_event_by_word_id(word_id, all_events):
    for event_id, event in all_events.items():
        left, right = event["span"]

        if left == word_id:
            return event_id

    raise ValueError(f"Event not found for word id {word_id}")


def convert_span_to_events(span, all_events, debug_info=None) -> Dict[str, dict]:
    """Returns events corresponding to the given span

    Args:
        all_events (dict): events dict with event ids as keys and dicts with "span" key as values,
            includes timexes (they just have a different prefix in the id)
        span (tuple): (start, end) span to convert to events, should include at least one event
        debug_info (str): optional debug info to be printed in case of error

    Returns:
        dict: events dict with event ids as keys and event dicts as values
    """
    debug_info = debug_info or ""
    return_events = {}

    for event_id, event in all_events.items():
        event_start, event_end = event["span"]  # 144, 144
        if event_start >= span[0] and event_end <= span[1]:
            return_events[event_id] = event

    if len(return_events) == 0:
        raise RuntimeError(f"{debug_info} No events found for span {span}")

    return return_events


def span_to_tuple(span):
    left, right = span
    assert type(left) == type(right) == int, f"Invalid event span: {span}"
    return (left, right)


def replace_consecutive_with_bounded(annotation):
    """C event is just a special case of B event, so we replace C events in the NT annotation dictionary with B events.
    The subspans of [C] are simply the spans of [B] events included in the [C] span

    This is how it is supposed to work:
        [C](E1 E2 E3, t=0) -> [B](E1, t=0), [B](E2, t=0 + eps), [B](E3, t=0 + 2*eps)
    (with a small enough epsilon to not get ahead of any other events)

    returns annotation dictionary with the same structure, but with [C] spans split into subspans
    """
    epsilon = 1e-4
    events = annotation["events"]
    timexes = annotation["timex"]
    event_order = annotation["event_order"]

    invisible_event_spans = set((word_id, word_id) for word_id in annotation["invisible_events"])
    new_event_order = {}

    for span_id, span_annotation in event_order.items():
        if span_annotation["event_type"] != NAME_TO_TYPE["[C]"]:
            new_event_order[span_id] = span_annotation
            continue

        # annotation checks
        if ":" in span_annotation["time"]:
            raise RuntimeError(f"[C] spans should not have an interval location: {span_annotation}")

        left, right = span_annotation["span"]

        included_timexes = [k for k, v in timexes.items() if v[0] >= left and v[1] <= right]
        assert len(included_timexes) == 0, f"[C] spans should not include temporal expressions: {span_annotation}"

        original_annotation_id = int(span_id)
        included_b_events = [k for k, v in events.items() if v[0] >= left and v[1] <= right]

        invluded_b_events_visible = []
        for event_id in included_b_events:
            event_span = span_to_tuple(events[event_id])
            if event_span not in invisible_event_spans:
                invluded_b_events_visible.append(event_id)

        for i, c_labelled_event in enumerate(invluded_b_events_visible, 1):
            modified_span_annotation = deepcopy(span_annotation)
            modified_span_annotation["span"] = events[c_labelled_event]
            modified_span_annotation["event_type"] = NAME_TO_TYPE["[B]"]
            modified_span_annotation["time"] = str(float(modified_span_annotation["time"]) + epsilon * i)
            new_event_order[str(original_annotation_id + epsilon * i)] = modified_span_annotation

    return new_event_order


def make_coreference_index(events, coreference):
    """
    Args:
        events: dict of events mapping event id to event dictionary (both events and timexes)
        coreference: dict of coreference mapping word id to list of coreferent word ids
    Returns:
        dict of coreference mapping event id to list of coreferent event ids
    """
    event_coreference_expanded = {}
    for k, coreferent_to_k in coreference.items():
        k = int(k)
        k_id = get_event_by_word_id(k, events)
        c_ids = [get_event_by_word_id(c, events) for c in coreferent_to_k]

        event_coreference_expanded[k_id] = c_ids
        for event in c_ids:
            coreferring_to_event = [k_id] + c_ids
            coreferring_to_event.remove(event)
            event_coreference_expanded[event] = coreferring_to_event
    return event_coreference_expanded


def convert_event_order_from_spans_to_events(event_order_spans, events_and_timexes, invisible_events=None):
    """
    Args:
        event_order_spans: dict of event order spans mapping event_order_id
            (just an arbitrary number, this have been a list) to event order dictionary.
            Original event_order from the annotation file.
        events_and_timexes: dict of events mapping event id to event dictionary (both events and timexes).
            These are the outputs of format_metadata merged together.
    Returns:
        dict of event order events mapping event order id to event order dictionary
    """
    invisible_events = invisible_events or []
    invisible_events = set(invisible_events)

    event_order_events = {}
    for span_annotation in event_order_spans.values():
        corresponding_events = convert_span_to_events(span_annotation["span"], events_and_timexes)  # this is where you can accidentally get invisible events

        # delete invisible events if they are in the span
        corresponding_events = {k: v for k, v in corresponding_events.items() if k not in invisible_events}

        if len(corresponding_events) == 0:
            # triggered when only an invisible event is in the span
            # this happens historically for A1 annotations because invisible_events were treated
            # differently in older version of the tool
            logger.warning(f"Span {span_annotation['span']} does not contain any visible events. Replacing with a hidden event under this span.")
            assert span_annotation["event_type"] != "[C]", "I hope this never happens, this would be a mess"
            _hidden_event = convert_span_to_events(span_annotation["span"], events_and_timexes)
            assert len(_hidden_event) == 1, "fallback error, please **carefuly** study the code above to understand this issue. It is probably a messy one."
            corresponding_events = _hidden_event

        for k, v in corresponding_events.items():
            _event_without_span = {k: v for k, v in span_annotation.items() if k != "span"}  # one span can include multiple events
            v_labelled = v | _event_without_span
            v_labelled["event_type"] = TYPE_TO_NAME[v_labelled["event_type"]]
            event_order_events[k] = v_labelled

    return event_order_events


def add_invisible_events_to_event_order(
        *,
        event_order,
        invisible_event_ids,
        event_coreference,
        events_and_timexes,
        debug_info=None,
    ):
    """
    Output example:
        {'t0': {'span': [5, 6], 'is_timex': True, 'type': '[B]', 'time': '1', 'relto': '', 'factuality': ''},
        'ei0': {'span': [94, 94], 'is_timex': False, 'eid': '0', 'type': '[U}', 'time': '-0.1', 'relto': '', 'factuality': ''},
    """
    event_coreference_index = make_coreference_index(events_and_timexes, event_coreference)
    event_order = deepcopy(event_order)

    for invisible_event_id in invisible_event_ids:
        coreferent_events = event_coreference_index[invisible_event_id]

        added_invisible_event = False
        for c in coreferent_events:
            if c not in event_order: continue
            added_invisible_event = True

            c_event_order_info = event_order[c]
            _event = deepcopy(events_and_timexes[invisible_event_id])
            _event["is_visible_during_annotation"] = False

            for k in ["event_type", "time", "branch", "factuality"]:
                assert k not in _event
                _event[k] = c_event_order_info[k]

            assert _event.keys() == c_event_order_info.keys(), f"{_event.keys()} != {c_event_order_info.keys()}"
            event_order[invisible_event_id] = _event

        if not added_invisible_event:
            raise RuntimeError(f"Could not find coreferent event for {invisible_event_id}")

    if len(events_and_timexes) != len(event_order):
        raise RuntimeError(f"Number of events and timexes does not match number of "
                           f"event order entries: {len(events_and_timexes)} != {len(event_order)}")

    return event_order


# Corpus offset is a problem for testing:
# we need to have exactly the same set of documents in the same order
# as when we wrote the tests
def format_metadata(data, corpus_offset):
    """Reformatting NT annotation for timex and event ids

    Input example: `{"0":[16,16],"1":[26,26]`
    Output example: `{'ei222': {'span': [16, 16], 'eid': 'e1', 'class': 'I_ACTION', 'pos': 'VERB', 'tense': 'PRESENT', 'aspect': 'PERFECTIVE', 'polarity': 'POS'}`
    (provided that TimeML metadata is available in "timex_refs"/"events_refs" keys. Otherwise new minimalistic tid/eid numbering is introduced)

    Args:
        data (dict): NT json data object
        corpus_offset (int): offset for generating running event instance ids
        across the whole corpus

    Returns:
        (dict, dict): events and timex dicts injected with metadata to be used in TimeML
    """

    timexes = data["timex"]
    timexes_reformatted = {}
    document_words = data["text"].split(" ")

    for t in timexes:
        span = timexes[t]
        _timex = {"span": span, "is_timex": True}

        if ADD_DEBUG_INFO:
            _text = " ".join(document_words[span[0]:span[1] + 1])
            _timex["text"] = _text
            _timex["doc_id"] = data["id"]

        if not "timex_refs" in data:
            tid = f"t{t}"
        else:
            _timex_meta = data["timex_refs"][t]
            tid = _timex_meta["tid"]
            for k in ["type", "value", "temporalFunction", "functionInDocument", "beginPoint", "endPoint", "quant", "freq", "value", "valueFromFunction", "mod", "anchorTimeID", "comment"]:
                if k in _timex_meta:
                    _timex[k] = _timex_meta[k]
        timexes_reformatted[tid] = _timex

    events = data["events"]
    event_refs = data.get("event_refs", None)
    events_reformatted = {}
    for event_id in events:
        extras = {}
        instance_extras = {}
        span = events[event_id]

        _text = " ".join(document_words[span[0]:span[1] + 1])
        _event = {"span": span, "is_timex": False}
        if ADD_DEBUG_INFO:
            _event["text"] = _text
            _event["doc_id"] = data["id"]

        if event_refs is None:
            eid = event_id
            eiid = f"ei{corpus_offset + int(event_id)}"

            _event["eid"] = eid
        else:
            # import ipdb; ipdb.set_trace()
            eid = event_refs[event_id]["eid"]
            eiid = event_refs[event_id]["eiid"]
            _event["eid"] = eid
            _event["eiid"] = eiid

            for k in ["class", "comment"]:
                if k in event_refs[event_id]:
                    extras[k] = event_refs[event_id][k]
            for k in ["eventID", "signalID", "pos", "tense", "aspect", "cardinality", "polarity", "modality", "comment"]:
                if k in event_refs[event_id]:
                    instance_extras[k] = event_refs[event_id][k]

        events_reformatted[eiid] = extras | instance_extras | _event

    return (events_reformatted, timexes_reformatted)


def get_events_and_timexes(annotation, corpus_offset=0, return_list=False):
    """Converts NT format into a common json format where each event/timex has all relevant information.

    Converts hidden events into visible ones by copying the information from the coreferent events.
    Converts both timexes and events into a common format (field "is_timex" is used to distinguish them).

    Args:
        annotation: narrative time annotation json of the form:
            id: ABC19980108.1830.0711
            text: str
            events:  # left and right are the word indices (split by " ") of the event
                dict[int, [left, right]]
                '0': [16, 16],
                '1': [22, 22],
                '2': [29, 29],
                ...
            timex:  # left and right are the word indices (split by " ") of the timex
                dict[int, [left, right]]
                '0': [1, 1],
                '1': [24, 24],
            event_order:  # NarratimeTime annotation; spans are char-level annotations contain one or more events
                dict[int, dict]
                '0': {'span': [0, 19], 'type': 0, 'time': '6', 'relto': '', 'factuality': ''},
                '1': {'span': [21, 26], 'type': 0, 'time': '5:6', 'relto': '', 'factuality': ''},
                ...
            event_coreference:  # word-level annotations of coreferring events
                '123': [120, 125],  # event at index 123 is coreferring with events at indices 120 and 125
                '165': [168, 746],
                '245': [251],  # event at index 245 is coreferring with event at index 251
                ...
            invisible_events:  # not visible during annotation, but time be inferred via event_coreference
                dict[int, [left, right]]
                '0': [16, 16],
                '1': [22, 22],
                '2': [29, 29],
                ...
    Returns:
        events_and_timexes: dict of events and timexes mapping event/timex id to event/timex dictionary

    Output example:
        {'t0': {'span': [5, 6], 'is_timex': True, 'type': '[B]', 'time': '1', 'relto': '', 'factuality': ''},
        'ei0': {'span': [94, 94], 'is_timex': False, 'eid': '0', 'type': '[U}', 'time': '-0.1', 'relto': '', 'factuality': ''},
    """
    _events, _timexes = format_metadata(annotation, corpus_offset=corpus_offset)
    events_and_timexes = {}
    for k, v in _events.items():
        v["is_timex"] = False
        events_and_timexes[k] = v

    for k, v in _timexes.items():
        assert k not in events_and_timexes, "timexes should have different ids from events"
        v["is_timex"] = True
        events_and_timexes[k] = v

    event_order = replace_consecutive_with_bounded(annotation)  # tricky part

    invisible_events = [get_event_by_word_id(word_id, events_and_timexes) for word_id in annotation["invisible_events"]]
    event_order = convert_event_order_from_spans_to_events(event_order, events_and_timexes, invisible_events=invisible_events)

    for k, v in event_order.items():
        v["is_visible_during_annotation"] = True  # useful for debugging, not used in the code

    events_and_timexes = add_invisible_events_to_event_order(
        event_order=event_order,
        invisible_event_ids=invisible_events,
        event_coreference=annotation["event_coreference"],
        events_and_timexes=events_and_timexes,
        debug_info=annotation,
    )

    if return_list:
        events_and_timexes_list = []
        for k, v in events_and_timexes.items():
            v["id"] = k
            events_and_timexes_list.append(v)
        return events_and_timexes_list

    return events_and_timexes
