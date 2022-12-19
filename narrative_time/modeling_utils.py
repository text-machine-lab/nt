import torch
import numpy as np

from transformers import PreTrainedTokenizerFast

from narrative_time import event_relations, conversion_utils
from narrative_time.event_relations import REL_TO_ID


def _make_event_vocab(soup):
    """Make a vocabulary of events/timexes.

    Extracts all eeid (from MAKEINSTANCE) and tid (from TIMEX3) and creates a
    vocabulary of events/timexes.

    Returns:
        event_vocab: a dictionary mapping event/timex ids to indices in the graph
    """
    # extract all eeid and tid
    eeid = set()
    tid = set()
    for elem in soup.find_all("MAKEINSTANCE"):
        eeid.add(elem["eiid"])
    for elem in soup.find_all("TIMEX3"):
        tid.add(elem["tid"])

    # create a vocabulary of events/timexes
    event_vocab = {}
    for i, e in enumerate(eeid.union(tid)):
        event_vocab[e] = i
    return event_vocab


def make_graph(soup, event_vocab=None):
    """Make a graph from TML soup object.

    Extracts all eeid (from MAKEINSTANCE) and tid (from TIMEX3) and creates a
    vocabulary of events/timexes. Then, for each event, it extracts all
    relations (from TLINK) and creates a graph.

    Args:
        soup: a soup object of a TML file
        event_vocab: (optional) a dictionary mapping event/timex ids to indices in the graph

    Returns:
        graph: a numpy array of shape (n_events, n_events)
        event_vocab: a dictionary mapping event/timex ids to indices in the graph
    """
    if event_vocab is None:
        event_vocab = _make_event_vocab(soup)

    # create a graph
    n_events = len(event_vocab)
    tlinks = soup.find_all("TLINK")
    assert len(tlinks) == n_events ** 2 - n_events

    graph = -1 * np.ones((n_events, n_events), dtype=np.int8)
    for tlink in tlinks:
        left = tlink.get("eventInstanceID")
        if left is None:
            left = tlink.get("timeID")

        if left is None:
            raise RuntimeError(tlink)

        right = tlink.get("relatedToEventInstance")
        if right is None:
            right = tlink.get("relatedToTime")

        if right is None:
            raise RuntimeError(tlink)

        assert graph[event_vocab[left], event_vocab[right]] == -1
        graph[event_vocab[left], event_vocab[right]] = REL_TO_ID[tlink["relType"]]

    # this approach to error is better for debugging
    error = None
    if np.any((graph + np.identity(n_events)) == -1):
        error = "Some relations are missing"

    return graph, event_vocab, error


class NTAnnotation:
    """A class representing a Narrative Time annotation.

    An `NTAnnotation` object contains information about the words in a document, the events and timexes mentioned in the
    document, and the relations between these events. It is typically created from a JSON dictionary returned by the
    Narrative Time annotation tool.

    Attributes:
        text (str): The text of the document.
        events_and_timexes (List[Dict]): (output of conversion_utils.get_events_and_timexes) A list of dictionaries representing events and timexes in the document.
            Each dictionary has the following keys:
                - span (List[int]): A list of two integers representing the start and end indices (inclusive) of the event
                  or timex span in the document text.
                - is_timex (bool): A boolean indicating whether the span corresponds to a timex (True) or an event (False).
                - eid (str): The event or timex identifier.
                - event_type (str): The event or timex type.
                - time (str): The time expression associated with the event or timex, if any.
                - relto (str): The event or timex to which this event or timex is related, if any.
                - factuality (str): The factuality of the event or timex.
                - id (str): The unique identifier for the event or timex.
        event_indices (List[str]): A list of event identifiers, in the same order as in `event_relation_matrix`.
        event_relation_matrix (np.ndarray): An array of shape (num_events, num_events) representing the relations between
            the events in the document. The i-th row and j-th column of the matrix contains the index of the relation
            between the i-th and j-th events in `event_indices`. The relation index is mapped from the `event_relations`
            module's `REL_TO_ID` dictionary.

    Example:
        >>> nt_annotation = NTAnnotation.from_json(json_dict)
        >>> print(nt_annotation)
        NTAnnotation(text='The cat sat on the mat.',
                     events_and_timexes=[{'span': [0, 3],
                                         'is_timex': False,
                                         'eid': '0',
                                         'event_type': '[B]',
                                         'time': '',
                                         'relto': '',
                                         'factuality': '',
                                         'id': 'ei0'},
                                        {'span': [12, 15],
                                         'is_timex': False,
                                         'eid': '1',
                                         'event_type': '[B]',
                                         'time': '',
                                         'relto': '',
                                         'factuality': '',
                                         'id': 'ei1'}],
                     event_relation_matrix=[[-1, 1],
                                            [2, -1]])
    """
    def __init__(self, doc_id, text, events_and_timexes, event_indices, event_relation_matrix):
        self.doc_id = doc_id
        self.text = text
        self.events_and_timexes = events_and_timexes
        self._event_indices = event_indices
        self.event_id_to_numeric_id = {event_id: i for i, event_id in enumerate(self._event_indices)}
        self.event_relation_matrix = event_relation_matrix

    @classmethod
    def from_json(cls, json_dict):
        text = json_dict["text"]
        doc_id = json_dict["id"]
        events_and_timexes = conversion_utils.get_events_and_timexes(json_dict, return_list=True)
        event_ids = [event["id"] for event in events_and_timexes]
        event_id_to_numeric_id = {event_id: i for i, event_id in enumerate(event_ids)}

        event_relation_matrix = -1 * np.ones((len(event_ids), len(event_ids)), dtype=np.int8)
        for i, left in enumerate(events_and_timexes):
            for j, right in enumerate(events_and_timexes):
                if i == j: continue

                relation = event_relations.get_event_relation(left, right)
                left_idx = event_id_to_numeric_id[left["id"]]
                right_idx = event_id_to_numeric_id[right["id"]]
                event_relation_matrix[left_idx, right_idx] = event_relations.REL_TO_ID[relation]

        return cls(doc_id, text, events_and_timexes, event_ids, event_relation_matrix)

    def __repr__(self):
        event_repr = (str(e) for e in self.events_and_timexes[:3])
        event_repr = "\n".join(event_repr)
        event_repr = "\n" + event_repr + "\n  ..."
        text_repr = self.text[:100].replace("\n", " ") + "..."
        return f"NTAnnotation(text={text_repr}\nevents_and_timexes={event_repr}\nevent_relation_matrix:\n{self.event_relation_matrix})"

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.events_and_timexes)


def preprocess_document(annotation: NTAnnotation, tokenizer: PreTrainedTokenizerFast):
    """Preprocess a document for event relation classification.

    This function takes a document represented as an `NTAnnotation` object, which contains information about the words in the
    document, the events and timexes mentioned in the document, and the relations between these events. The function performs
    several steps to prepare the document for event relation classification:
    
        1. Tokenize the words in the document using a tokenizer.
        2. Convert the word-level spans of events and timexes to token-level spans.
        3. Convert the list of events and timexes, and the event relation matrix, into tensors suitable for input to a model.

    Args:
        annotation: An `NTAnnotation` object representing the document to be preprocessed.

    Returns:
        A tuple containing the following elements:
            - input_ids: A tensor of shape (num_tokens, ) representing the tokenized words in the document.
            - event_left_tokens: A tensor of shape (num_events, ) representing the indices of the leftmost tokens in the
              spans of the events in the document.
            - event_relation_matrix: A tensor of shape (num_events, num_events) representing the relations between the
              events in the document.

    Raises:
        AssertionError: If the text of an event or timex span as reconstructed from the word-level span does not match the
                        text of the same span reconstructed from the token-level span.
        AssertionError: If the order of events in the input `annotation` object is not the same as the order of events in
                        the output `event_relation_matrix`.
    """
    # Tokenize the words in the document and fix the word-level spans of events and timexes.
    text = annotation.text
    text = text.replace("`", "'")  # some tokenizers (e.g., long-t5 tokenizer) don't handle backticks correctly
    TOKEN_BLOCKLIST = {"", "\n", " "}  # it's extremely important that we remove these tokens from the input to make sure the indices line up

    words = []
    original_pos_to_fixed_pos = {}
    for i, word in enumerate(text.split(" ")):
        # if word == "": continue
        if word in TOKEN_BLOCKLIST: continue
        words.append(word)
        original_pos_to_fixed_pos[i] = len(words) - 1

    # Prepare alignment between word-level and token-level spans.
    inputs = tokenizer(words, is_split_into_words=True)
    word_ids = inputs.word_ids()

    word_set = set(word_ids)
    word2left_index = []
    for i in range(len(words)):
        if i not in word_set: continue
        word2left_index.append(word_ids.index(i))

    word2right_index = []
    word_ids_reversed = word_ids[::-1]
    for i in range(len(words)):
        if i not in word_set: continue
        index = len(word_ids_reversed) - word_ids_reversed.index(i) - 1
        assert index >= 0
        word2right_index.append(index)

    input_ids = inputs.input_ids

    def word_span_to_token_span(word_span):
        left, right = word_span

        left = word2left_index[left]
        right = word2right_index[right]
        return left, right

    # Check that the text of an event or timex span as reconstructed from the word-level span matches the text of the same.
    for event in annotation.events_and_timexes:
        word_span = event["span"]
        word_span = original_pos_to_fixed_pos[word_span[0]], original_pos_to_fixed_pos[word_span[1]]
        token_span = word_span_to_token_span(word_span)

        text_from_word_span = " ".join(words[word_span[0]:word_span[1]+1])

        token_span_ids = input_ids[token_span[0]:token_span[1]+1]
        text_from_token_span = tokenizer.decode(token_span_ids).strip(" ")

        assert text_from_word_span == text_from_token_span, f"`{text_from_word_span}` != `{text_from_token_span}`. {word_span} != {token_span}"

    # Convert the word-level spans of events and timexes to token-level spans.
    event_left_tokens = []
    event_ids = []
    for event in annotation.events_and_timexes:
        word_span = event["span"]
        word_span = original_pos_to_fixed_pos[word_span[0]], original_pos_to_fixed_pos[word_span[1]]
        token_span = word_span_to_token_span(word_span)
        event_left_tokens.append(token_span[0])

        event_id = annotation.event_id_to_numeric_id[event["id"]]
        event_ids.append(event_id)
    
    assert event_ids == list(range(len(event_ids))), "guarantees that the order of events is the same as in annotation.event_relation_matrix"

    input_ids = torch.tensor(input_ids, dtype=torch.long)
    event_left_tokens = torch.tensor(event_left_tokens, dtype=torch.long)
    event_relation_matrix = torch.tensor(annotation.event_relation_matrix, dtype=torch.long)


    return input_ids, event_left_tokens, event_relation_matrix
