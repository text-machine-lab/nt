"""Narrative time interval to TLINK conversion logic

Handles conversion of interval types ([], [}, {], {}) and intervals into relations.
"""

from collections import defaultdict
from collections import namedtuple

Interval = namedtuple("Interval", ["start", "end"])

REL_TO_ID = {
    "BEFORE": 0,
    "AFTER": 1,
    "INCLUDES": 2,
    "IS_INCLUDED": 3,
    "SIMULTANEOUS": 4,
    "OVERLAP": 5,
    "VAGUE": 6,
}

ALLOWED_TYPES = {"[B]", "{U}", "{U]", "[U}"}
SPECIAL_SYMBOLS = "!@#$%^&*?"  # do not add < and > here, it will break the code
CONVERION_TABLE = {
    ("[B]", "[B]"): {
        "BEFORE": "BEFORE",
        "AFTER": "AFTER",
        "INCLUDES": "INCLUDES",
        "IS_INCLUDED": "IS_INCLUDED",
        "OVERLAP_BEFORE": "OVERLAP",
        "OVERLAP_AFTER": "OVERLAP",
        "SIMULTANEOUS": "SIMULTANEOUS",
    },
    ("{U}", "{U}"): defaultdict(lambda: "VAGUE"),
    ("[U}", "[U}"): defaultdict(lambda: "VAGUE"),
    ("{U]", "{U]"): defaultdict(lambda: "VAGUE"),
    ("[B]", "{U}"): defaultdict(
        lambda: "VAGUE", {
        "IS_INCLUDED": "IS_INCLUDED",
        "SIMULTANEOUS": "IS_INCLUDED",
    }),
    ("{U}", "[B]"): defaultdict(
        lambda: "VAGUE", {
        "INCLUDES": "INCLUDES",
        "SIMULTANEOUS": "INCLUDES",
    }),
    ("[B]", "[U}"): defaultdict(
        lambda: "VAGUE", {
        "BEFORE": "BEFORE",
        "IS_INCLUDED": "IS_INCLUDED",
        "OVERLAP_BEFORE": "OVERLAP",
        "SIMULTANEOUS": "IS_INCLUDED",
    }),
    ("[U}", "[B]"): defaultdict(
        lambda: "VAGUE", {
        "AFTER": "AFTER",
        "INCLUDES": "INCLUDES",
        "OVERLAP_AFTER": "OVERLAP",
        "SIMULTANEOUS": "INCLUDES",
    }),
    ("[B]", "{U]"): defaultdict(
        lambda: "VAGUE", {
        "AFTER": "AFTER",
        "IS_INCLUDED": "IS_INCLUDED",
        "OVERLAP_AFTER": "OVERLAP",
        "SIMULTANEOUS": "IS_INCLUDED",
    }),
    ("{U]", "[B]"): defaultdict(
        lambda: "VAGUE", {
        "BEFORE": "BEFORE",
        "INCLUDES": "INCLUDES",
        "OVERLAP_BEFORE": "OVERLAP",
        "SIMULTANEOUS": "INCLUDES",
    }),
    ("{U}", "[U}"): defaultdict(
        lambda: "VAGUE", {
        "INCLUDES": "INCLUDES",
        "SIMULTANEOUS": "INCLUDES",
    }),
    ("[U}", "{U}"): defaultdict(
        lambda: "VAGUE", {
        "IS_INCLUDED": "IS_INCLUDED",
        "SIMULTANEOUS": "IS_INCLUDED",
    }),
    ("{U}", "{U]"): defaultdict(
        lambda: "VAGUE", {
        "INCLUDES": "INCLUDES",
        "SIMULTANEOUS": "INCLUDES",
    }),
    ("{U]", "{U}"): defaultdict(
        lambda: "VAGUE", {
        "IS_INCLUDED": "IS_INCLUDED",
        "SIMULTANEOUS": "IS_INCLUDED",
    }),
    ("{U]", "[U}"): defaultdict(
        lambda: "VAGUE", {
        "BEFORE": "BEFORE",
        "OVERLAP_BEFORE": "OVERLAP",
        "SIMULTANEOUS": "OVERLAP",
    }),
    ("[U}", "{U]"): defaultdict(
        lambda: "VAGUE", {
        "AFTER": "AFTER",
        "OVERLAP_AFTER": "OVERLAP",
        "SIMULTANEOUS": "OVERLAP",
    }),
}


def get_event_relation(event1, event2):
    """Get relation between two events.
    
    Args:
        event1: dict with keys "time" and "event_type"
        event2: dict with keys "time" and "event_type"
    
    Returns:
        str: relation between events, one of "BEFORE", "AFTER", "INCLUDES", "IS_INCLUDED", "OVERLAP", "SIMULTANEOUS", "VAGUE"
    """
    type1, type2 = event1["event_type"], event2["event_type"]

    interval1 = to_interval(event1["time"], type_=event1["event_type"])
    interval2 = to_interval(event2["time"], type_=event2["event_type"])

    # special case {:} vs {:} is OVERLAP
    if type1 == "{U}" and type2 == "{U}" and interval1 == interval2 == Interval(float("-inf"), float("inf")):
        return "OVERLAP"

    interval1, interval2 = interval1, interval2
    interval_relation = get_interval_relation(interval1, interval2)

    return CONVERION_TABLE[(type1, type2)][interval_relation]


def get_event_relation_separate_branches(event1, event2):
    """Get relation between two events in separate branches.
    
    Events on separate branches are almost always VAGUE, the exceptions are:

    A AFTER B: B merges into A before A starts: ------------A-
                                                ---B---^

    A BEFORE B: B branches off after A ends: ----A---|-----
                                                     |--B---

    A INCLUDES B: A is an uncentered unbounded event and B branches off any time
    B IS_INCLUDED A: A is an uncentered unbounded event and B merges into A any time

    Note that if unbounded interval is permanent (not centered), then relation between
    different branches is always VAGUE.

    Also, because there are multiple branches that branch off off the main timeline,
    we need to convert the branch to an interval on the main timeline
    (main timeline is special because branches can only branch off of it)

    Here's how conversion works:
        1. Get position of each event on the main timeline:
           it is either the position of the event itself, or the position of the branch
        2. We use the Interval abstraction to get the position of each event on the main timeline.
           It converts branch >5 into [5, +inf] and branch <5 into [-inf, 5].
        3. Now we can compare the two intervals and get the relation between them.
           If it is anything other than BEFORE or AFTER, return VAGUE.
           Else, return the relation.

    Args:
        event1: dict with keys "time", "event_type", "branch"
        event2: dict with keys "time", "event_type", "branch"
    
    Returns:
        str: BEFORE, AFTER, VAGUE
    """
    branch1 = event1["branch"]
    branch2 = event2["branch"]

    if branch1 == branch2:
        raise ValueError("use get_event_relation() for events in the same branch")

    # note special flag treat_unbounded_as_infitine
    # it is used specifically for between-interval relations
    interval1 = to_interval(event1["time"], type_=event1["event_type"], treat_unbounded_as_infitine=True)
    interval2 = to_interval(event2["time"], type_=event2["event_type"], treat_unbounded_as_infitine=True)

    if event1["event_type"] == "{U}" and event1["time"] in ["", ":"]:
        return "INCLUDES"

    if event2["event_type"] == "{U}" and event2["time"] in ["", ":"]:
        return "IS_INCLUDED"

    if event1["event_type"] == "{U}" and is_finite(interval1):
        return "VAGUE"

    if event2["event_type"] == "{U}" and is_finite(interval2):
        return "VAGUE"

    # get position of each event on the main timeline
    if branch1 != "":
        branch1_interval = branch_to_interval(branch1)
        interval1 = merge_event_and_branch_intervals(interval1, branch1_interval)

    if branch2 != "":
        branch2_interval = branch_to_interval(branch2)
        interval2 = merge_event_and_branch_intervals(interval2, branch2_interval)

    interval_relation = get_interval_relation(interval1, interval2)

    if interval_relation not in ["BEFORE", "AFTER"]:
        return "VAGUE"

    return interval_relation


def merge_event_and_branch_intervals(event_interval, branch_interval):
    """Merge event and branch intervals.
    
    Args:
        event_interval: Interval
        branch_interval: Interval
    
    Returns:
        Interval: merged interval
    """
    if event_interval.start == float("-inf"):
        return Interval(float("-inf"), branch_interval.end)

    if event_interval.end == float("inf"):
        return Interval(branch_interval.start, float("inf"))

    return branch_interval


def get_interval_relation(time1, time2):
    """Look at the relation between time intervals ignoring interval types.
    For example:
        1-3	4-6: BEFORE
        4-6	1-3: AFTER
        1-6	3-4: INCLUDES
        3-4	1-6: IS_INCLUDED
        1-4	3-6: OVERLAP_BEFORE
        3-6	1-4: OVERLAP_AFTER
        1-3	1-3: SIMULTANEOUS
    """
    # [L.start == R.start] [L.end == R.end]
    if time1.start == time2.start and time1.end == time2.end:
        return "SIMULTANEOUS"

    # [L.start L.end] {R.start R.end}
    if time1.end <= time2.start:
        return "BEFORE"

    # {R.start R.end} [L.start L.end]
    if time1.start >= time2.end:
        return "AFTER"

    # [L.start {R.start R.end} L.end]
    if time1.start <= time2.start and time2.end <= time1.end:
        return "INCLUDES"

    # {R.start [L.start L.end] R.end}
    if time2.start <= time1.start and time1.end <= time2.end:
        return "IS_INCLUDED"

    # [L.start {R.start L.end] R.end}
    if time1.start <= time2.start and time1.end <= time2.end:
        return "OVERLAP_BEFORE"

    # {R.start L.start} [L.end R.end}
    if time2.start <= time1.start and time2.end <= time1.end:
        return "OVERLAP_AFTER"

    raise ValueError(f"Can't classify {time1} and {time2}")


def to_interval(time, type_, treat_unbounded_as_infitine=False):
    """Convert event to interval with both ends.

    E.g. "1" -> Interval[1, 1], "1:2" -> Interval[1, 2]

    Args:
        treat_unbounded_as_infitine: if True, returns -inf for { and +inf for } (for partially bounded only)
            used for between-branch event conversions, on-branch partially bounded events should be compared
            with treat_unbounded_as_infitine=False.
    """
    assert type_ in ALLOWED_TYPES, type_
    left_bracket, right_bracket = type_[0], type_[-1]

    if time in ["", ":"]:
        if type_ != "{U}": raise ValueError(f"{time} and {type_} are not compatible.")
        return Interval(float("-inf"), float("inf"))

    if ":" in time:
        start, end = time.split(":")
        return Interval(float(start), float(end))

    if not treat_unbounded_as_infitine:
        return Interval(float(time), float(time))

    if type_ == "{U}":
        # special case, while for {2] we give Interval[-inf, 2]
        # for {2} we give Interval[2, 2]
        return Interval(float(time), float(time))

    start = float(time) if left_bracket == "[" else float("-inf")
    end = float(time) if right_bracket == "]" else float("inf")

    return Interval(start, end)


def is_finite(event_type):
    """Check if interval is finite (not infinite)"""
    return "{" not in event_type and "}" not in event_type


def branch_to_interval(branch):
    """Converts branch of the form "6>" (may contain special symbols) to Interval

    For example:
        6> -> Interval[6, inf]
        6>? -> Interval[6, inf]
        <10 -> Interval[-inf, 10]
        <6 -> Interval[-inf, 6]
    """
    for symbol in SPECIAL_SYMBOLS:
        branch = branch.replace(symbol, "")

    if ">" in branch:
        start = float(branch.replace(">", ""))
        end = float("inf")
        return Interval(start, end)

    if "<" in branch:
        start = float("-inf")
        end = float(branch.replace("<", ""))
        return Interval(start, end)

    raise ValueError(f"Can't convert {branch} to interval")
