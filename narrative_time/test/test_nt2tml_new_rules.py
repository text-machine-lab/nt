# Same as test_nt2tml.py, but with the new rules from
# https://docs.google.com/spreadsheets/d/1wAhWUTkyii5NYedwGzplgGVMT1odVoF3WPfUAfRNniI
import os
import sys
import json
import shutil
import unittest

from bs4 import BeautifulSoup

# 1. script requires you to be in the script directory, because it relies on relative paths to the data
# 2. add ".." to be able to import nt2tml_v2
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)
sys.path.append(os.path.join(dir_path, "../../utils"))

from nt2tml import parse_nt_json


def test_tlinks(all_relations, all_soups, bidirectional=True, timex=False):
    """helper function for running tests on dictionaries of relations and """
    target_attr = "relatedToEventInstance"
    if timex:
        target_attr = "relatedToTime"

    all_checks_passed = True
    error_msg = "\n"
    n_errors = 0
    n_relations_tested = 0

    for id in all_relations.keys():
        relations = all_relations[id]
        soup = all_soups[id]
        for relation in relations.keys():
            pairs = relations[relation]
            for left, right, desc in pairs:
                pair = (left, right)

                n_relations_tested += 1
                found_relations = soup.findAll("TLINK", {"eventInstanceID": left, target_attr: right})
                if not found_relations and bidirectional:
                    found_relations = soup.findAll("TLINK", {"eventInstanceID": right, target_attr: left})
                if len(found_relations) > 1:
                    all_checks_passed = False
                    n_errors += 1
                    error_msg += f"Too many relations between {pair}: {[x['relType'] for x in found_relations]}\n"
                elif not found_relations:
                    all_checks_passed = False
                    n_errors += 1
                    error_msg += f"No {relation} relation between {pair} in doc {id}. Expected: {desc}. \n"
                else:
                    found_relation = found_relations[0]
                    if found_relation["relType"] != relation:
                        all_checks_passed = False
                        n_errors += 1
                        error_msg += f"Wrong relation between {pair}: {found_relation['relType']}. Expected: {desc}. \n"

    if not all_checks_passed:
        error_msg += f"Tested {n_relations_tested} relations, found {n_errors} errors.\n"

    return all_checks_passed, error_msg


class TestConversionScriptSucceeds(unittest.TestCase):
    def test01_conversion_script_works(self):
        parse_nt_json(
            input_file="test_new_rules.jsonl",
            output_dir="converted",
        )

    def test02_bs4_can_parse(self):
        """is the XML output overall valid (parse-able by BS4)?"""
        with open("test_new_rules.jsonl") as f:
            data = f.read().strip().split("\n")
        ids = [json.loads(x)["id"] for x in data]

        for id in ids:
            fpath = f"converted/{id}.tml"
            with open(fpath, "r") as file:
                content = "".join(file.readlines())
            try:
                BeautifulSoup(content, features="lxml-xml")
            except Exception as e:
                assert False, f"Could not parse {fpath}: {e}"
        
        shutil.rmtree("converted")


class TestTlinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """storing the parsed XML object"""
        if os.path.exists("converted"):
            shutil.rmtree("converted")  # delete the state from the previous test

        parse_nt_json(
            input_file="test_new_rules.jsonl",
            output_dir="converted",
        )

        with open("test_new_rules.jsonl") as f:
            data = f.read().strip().split("\n")

        cls.ids = [json.loads(x)["id"] for x in data]
        cls.soups = cls.get_soups(cls.ids)

    @staticmethod
    def get_soups(ids):
        soups = {}
        for id in ids:
            with open(f"converted/{id}.tml", "r") as file:
                content = "".join(file.readlines())
            soup = BeautifulSoup(content, features="lxml-xml")
            soups[id] = soup
        return soups
    
    def test_tlink_count(self):
        """test that the number of TLINKs in the output is makes a fully-connected graph
        
        Number of nodes in a fully-connected graph: N^2 - N (all connections but diagonal)
        """
        for doc_id, soup in self.soups.items():
            n_events = len(soup.findAll("EVENT")) + len(soup.findAll("TIMEX3"))

            expected_tlinks = n_events ** 2 - n_events
            n_tlinks = len(soup.findAll("TLINK"))
            self.assertEqual(
                n_tlinks, expected_tlinks,
                f"Wrong number of TLINKs in {doc_id}: {n_tlinks} (expected {expected_tlinks})"
            )

    # ---------------- [] vs [] ----------------
    def test_bounded_bounded_before_after(self):
        relations = {
            "ABC19980120.1830.0957": {
                "BEFORE": [
                    ("ei77", "ei78", "[1] predicted BEFORE [1.5] demise"),
                ],
                "AFTER": [
                    ("ei78", "ei77", "[1.5] demise AFTER [1] predicted"),
                ],
            },
        }
        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_bounded_bounded_includes_is_included(self):
        relations = {
            "ABC19980120.1830.0957": {
                "INCLUDES": [
                    ("ei96", "ei121", "[0:3.5] embargo INCLUDES [2:3] risk"),
                ],
                "IS_INCLUDED": [
                    ("ei121", "ei96", "[2:3] risk IS_INCLUDED [0:3.5] embargo"),
                ],
            },
        }
        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_bounded_bounded_overlap(self):
        relations = {
            "ABC19980120.1830.0957": {
                "OVERLAP": [
                    ("ei96", "ei108", "[0:3.5] embargo OVERLAP [3:7] led"),
                    ("ei108", "ei96", "[3:7] led OVERLAP [0:3.5] embargo"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_bounded_bounded_simultaneous(self):
        relations = {
            "ABC19980120.1830.0957": {
                "SIMULTANEOUS": [
                    ("ei96", "ei97", "[0:3.5] embargo SIMULTANEOUS [0:3.5] kept"),  # same span
                    ("ei97", "ei96", "[0:3.5] kept SIMULTANEOUS [0:3.5] embargo"),  # same span
                    ("ei96", "ei95", "[0:3.5] embargo SIMULTANEOUS [0:3.5] rule"),  # different spans
                    ("ei95", "ei96", "[0:3.5] rule SIMULTANEOUS [0:3.5] embargo"),  # different spans
                ],
            }
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    # ---------------- {} vs [] ----------------
    def test_unbounded_bounded_includes(self):
        relations = {
            "ABC19980120.1830.0957": {
                "INCLUDES": [
                    ("ei119", "ei77", "{} exploitation INCLUDES [1] predicted"),
                    ("ei119", "ei96", "{} exploitation INCLUDES [0:3.5] embargo"),
                ],
            },
            "ABC19980108.1830.0711": {
                "INCLUDES": [
                    ("ei19", "ei21", "{4} construction INCLUDES [4] backed"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    # ---------------- [] vs {} ----------------
    def test_bounded_unbounded_is_included(self):
        relations = {
            "ABC19980120.1830.0957": {
                "IS_INCLUDED": [
                    ("ei77", "ei119", "[1] predicted IS_INCLUDED in {} exploitation"),    # bounded in unbounded
                    ("ei96", "ei119", "[0:3.5] embargo IS_INCLUDED in {} exploitation"),  # long bounded in unbounded
                ],
            },
            "ABC19980108.1830.0711": {
                "IS_INCLUDED": [
                    ("ei21", "ei19", "[4] backed IS_INCLUDED in {4} construction"),  # bounded in unbounded
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    # ---------------- [] vs [} ----------------
    def test_bounded_partially_bounded_before(self):
        relations = {
            "ABC19980108.1830.0711": {
                "BEFORE": [
                    ("ei21", "ei31", "[4] backed BEFORE [6} believe"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_bounded_partially_bounded_is_included(self):
        relations = {
            "ABC19980108.1830.0711": {
                "IS_INCLUDED": [
                    ("ei44", "ei31", "[6] gloomy IS_INCLUDED [6} believe"),
                ],
            }
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg
    
    def test_bounded_partially_bounded_vague(self):
        relations = {
            "AP900815-0044": {
                "VAGUE": [
                    ("ei340", "ei156", "[1] held VAGUE [-0.1} facing"),
                ],
            },
            "APW19980219.0476": {
                "VAGUE": [
                    ("ei742", "ei810", "[-15.5} presumed VAGUE [-14] defection"),
                    ("ei810", "ei742", "[-14] defection VAGUE in [-15.5} presumed"),
                ],
            },
            "APW19980213.1320": {
                "VAGUE": [
                    ("ei680", "ei673", "{4] flights (a week) VAGUE [2] suspended"),
                    ("ei673", "ei680", "[2] suspended VAGUE {4] flights (a week)"),
                ],
            },
            "APW19980213.1310": {
                "VAGUE": [
                    ("ei646", "ei629", "[-4.5:12] independent VAGUE {2] war"),
                    ("ei629", "ei646", "{2] war VAGUE [-4.5:12] independent"),
                ],
            },
            "CNN19980227.2130.0067": {
                "VAGUE": [
                    ("ei908", "ei877", "[2} claim VAGUE [1:3] related"),
                    ("ei877", "ei908", "[1:3] related VAGUE [2} claim"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    # ---------------- [} vs [] ----------------
    def test_partially_bounded_bounded_after(self):
        relations = {
            "ABC19980108.1830.0711": {
                "AFTER": [
                    ("ei31", "ei21", "[6} believe AFTER [4] backed"),
                ],
            },
            "APW19980213.1310": {
                "AFTER": [
                    ("ei626", "ei629", "[4:10] (monarchists) hope AFTER {2] war"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    # ---------------- {] vs [] and [] vs [} ----------------
    def test_partially_bounded_bounded_before(self):
        relations = {
            "APW19980213.1320": {
                "BEFORE": [
                    ("ei680", "ei668", "{4] flights (a week) BEFORE [4.5] double"),
                ],
            },
            "ABC19980108.1830.0711": {
                "BEFORE": [
                    ("ei13", "ei31", "[2] spent BEFORE [6} believe (this)"),
                ],
            }
        }
        # TODO: add a branched future case?

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        return all_checks_passed, error_msg

    # ---------------- [} vs [] and {] vs [] ----------------
    def test_partially_bounded_bounded_includes(self):
        raise NotImplementedError()

    def test_partially_bounded_bounded_is_included(self):
        raise NotImplementedError()
    
    def test_partially_bounded_unbounded_is_included(self):
        relations = {
            "APW19980213.1320": {
                "IS_INCLUDED": [
                    ("ei680", "ei670", "{4] flights (a week) IS_INCLUDED in {} untouched"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_partially_bounded_bounded_overlap(self):
        """In terms of the conversion table, this test covers 4 cases:
            - case 1: [1:4] OVERLAP [3:6}
            - case 2: [3:6} OVERLAP [1:4]
            - case 3: [3:6] OVERLAP {1:4]
            - case 4: {1:4] OVERLAP [3:6]
        """
        raise NotImplementedError()

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    # ---------------- {} vs [} and {} vs {] ----------------
    def test_unbounded_partially_bounded_vague(self):
        relations = {
            "ABC19980108.1830.0711": {
                "VAGUE": [
                    ("ei19", "ei31", "{4} construction VAGUE [6} believe"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_permanent_unbounded_partially_bounded_includes_is_included(self):
        relations = {
            "ABC19980108.1830.0711": {
                "INCLUDES": [
                    ("ei30", "ei31", "{} going INCLUDES [6} believe"),
                ],
                "IS_INCLUDED": [
                    ("ei31", "ei30", "[6} believe IS_INCLUDED in {} going"),
                ],
            }
        }
        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_partially_bounded_unbounded_vague(self):
        # this test used to be "is_included", but after looking at the
        # conversion table, I think it should be "vague"
        # we currently have no test for is included case,
        # but looking at the rest of the the tests of the final script, we should be good to go
        relations = {
            "ABC19980108.1830.0711": {
                "VAGUE": [
                    ("ei31", "ei19", "[6} believe VAGUE {4} construction"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg
    
    # ---------------- {] vs [} and {] vs {] ----------------
    def test_partially_bounded_partially_bounded_before(self):
        relations = {
            "NYT19980206.0460": {
                "BEFORE": [
                    ("ei940", "ei954", "{3] demand (for workers) BEFORE [7.5} (economy to) slow"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg
    
    def test_partially_bounded_partially_bounded_after(self):
        relations = {
            "NYT19980206.0460": {
                "AFTER": [
                    ("ei954", "ei940", "[7.5} (economy to) slow AFTER {3] demand (for workers)"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_partially_bounded_partially_bounded_overlap(self):
        raise NotImplementedError()

    def test_partially_bounded_partially_bounded_vague(self):
        relations = {
            "APW19980213.1310": {
                "VAGUE": [
                    ("ei629", "ei660", "{2] war VAGUE [-4.5:4} has (for almost a hundred years)"),
                    ("ei660", "ei629", "[-4.5:4} has (for almost a hundred years) VAGUE {2] war"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    # Misc
    def test_future_branch_bounded_vague(self):
        """E.g., [1] 4> and [10] should be VAGUE"""
        relations = {
            "ABC19980108.1830.0711": {
                "VAGUE": [
                    ("ei18", "ei31", "([1] on branch 3>) double VAGUE [6} believe"),
                ],
            },
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

# APW19980213.1320 ei671 [1:2} crisis
# APW19980213.1320 ei673 [2] suspended
# APW19980213.1320 ei680 {4] flights (a week)

if __name__ == "__main__":
    unittest.main()
