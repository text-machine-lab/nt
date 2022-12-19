import unittest

from narrative_time.event_relations import to_interval, get_event_relation_separate_branches, Interval


class TestToInterval(unittest.TestCase):

    def test_bounded(self):
        assert to_interval("1", "[B]") == Interval(1, 1)
        assert to_interval("1:2", "[B]") == Interval(1, 2)

    def test_unbounded(self):
        assert to_interval("", "{U}") == Interval(float("-inf"), float("inf"))
        assert to_interval(":", "{U}") == Interval(float("-inf"), float("inf"))
        assert to_interval("1", "{U}") == Interval(1, 1)
        assert to_interval("-1", "{U}") == Interval(-1, -1)
        assert to_interval("1:2", "{U}") == Interval(1, 2)

    def test_partially_bounded(self):
        assert to_interval("-0.1", "{U]") == Interval(-0.1, -0.1)
        assert to_interval("0.1", "{U]") == Interval(0.1, 0.1)
        assert to_interval("0.1", "[U}") == Interval(0.1, 0.1)


class TestGetEventRelatinSeparateBranches(unittest.TestCase):
    def test_before(self):
        event1 = {"time": "1", "event_type": "[B]", "branch": ""}
        event2 = {"time": "2", "event_type": "[B]", "branch": ">2"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "BEFORE")

    def test_before_negative(self):
        event1 = {"time": "-1", "event_type": "[B]", "branch": ""}
        # note that even second event has tml less than first, it is still AFTER
        event2 = {"time": "-2", "event_type": "[B]", "branch": ">-0.1"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "BEFORE")

    def test_vague_negative(self):
        event1 = {"time": "-1", "event_type": "[B]", "branch": ""}
        event2 = {"time": "-10", "event_type": "[B]", "branch": ">-2"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "VAGUE")

    def test_after(self):
        event1 = {"time": "2", "event_type": "[B]", "branch": ""}
        event2 = {"time": "1", "event_type": "[B]", "branch": "<1"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "AFTER")

    def test_after_different_branch_order(self):
        event1 = {"time": "2", "event_type": "[B]", "branch": ">2"}
        event2 = {"time": "1", "event_type": "[B]", "branch": ""}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "AFTER")
    
    def test_before_no_main_branch_bounded(self):
        event1 = {"time": "2", "event_type": "[B]", "branch": "<5"}
        event2 = {"time": "1", "event_type": "[U}", "branch": ">6?"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "BEFORE")

    def test_before_no_main_branch_unbounded(self):
        event1 = {"time": "2", "event_type": "[B]", "branch": "<5"}
        event2 = {"time": "1", "event_type": "{U}", "branch": ">6?"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "VAGUE")

    def test_vague_branches_start_at_the_same_time(self):
        event1 = {"time": "2", "event_type": "[B]", "branch": ">6$"}
        event2 = {"time": "2", "event_type": "{U}", "branch": ">6!"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "VAGUE")

    def test_reverse(self):
        event1 = {"time": "1", "event_type": "[B]", "branch": ""}
        event2 = {"time": "2", "event_type": "[B]", "branch": ">2"}

        self.assertEqual(get_event_relation_separate_branches(event2, event1), "AFTER")

    def test_centered_unbounded_on_main_line_vague(self):
        event1 = {"time": "2", "event_type": "{U}", "branch": ""}
        event2 = {"time": "2", "event_type": "[B]", "branch": ">2"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "VAGUE")

    def test_permanent_unbounded_on_main_line_vague(self):
        event1 = {"time": ":", "event_type": "{U}", "branch": ""}
        event2 = {"time": "2", "event_type": "[B]", "branch": ">2"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "INCLUDES")

    def test_partially_bounded_on_main_line_vague(self):
        event1 = {"time": "0.1", "event_type": "[U}", "branch": ""}
        event2 = {"time": "2", "event_type": "[B]", "branch": ">2"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "VAGUE")

    def test_partially_bounded_on_main_line_before(self):
        event1 = {"time": "0.1", "event_type": "{U]", "branch": ""}
        event2 = {"time": "0.2", "event_type": "[B]", "branch": ">2"}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "BEFORE")

    def test_partially_bounded_on_branch_after(self):
        event1 = {"time": "0.1", "event_type": "[U}", "branch": ">2"}
        event2 = {"time": "0", "event_type": "[B]", "branch": ""}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "AFTER")

    def test_partially_bounded_on_branch_vague(self):
        event1 = {"time": "0.1", "event_type": "{U]", "branch": ">2"}
        event2 = {"time": "0", "event_type": "[B]", "branch": ""}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "VAGUE")

    def test_double_partially_bounded_on_branch_vague(self):
        event1 = {"time": "0.1", "event_type": "{U]", "branch": "2<"}
        event2 = {"time": "10", "event_type": "{U]", "branch": ""}

        self.assertEqual(get_event_relation_separate_branches(event1, event2), "VAGUE")
