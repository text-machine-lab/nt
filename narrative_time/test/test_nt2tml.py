import os
import itertools
import unittest

from bs4 import BeautifulSoup


# id2type = {0: "[B]", 1: "[C]", 2: "{U}", 3: "[U}", 4: "{U]", 5: "[R>", 6: "<R]", 7: "[I]"}


def test_tlinks(all_relations, all_soups, bidirectional=True, timex=False):
    """helper function for running tests on dictionaries of relations and """
    target_attr = "relatedToEventInstance"
    if timex:
        target_attr = "relatedToTime"
    all_checks_passed = True
    error_msg = "\n"
    for id in all_relations:
        relations = all_relations[id]
        soup = all_soups[id]
        for relation in relations:
            pairs = relations[relation]
            for pair in pairs:
                found_relations = soup.findAll("TLINK", {"eventInstanceID": pair[0], target_attr: pair[1]})
                if not found_relations and bidirectional:
                    found_relations = soup.findAll("TLINK", {"eventInstanceID": pair[1], target_attr: pair[0]})
                if len(found_relations) > 1:
                    all_checks_passed = False
                    error_msg += f"Too many relations between {pair}: {[x['relType'] for x in found_relations]}\n"
                elif not found_relations:
                    all_checks_passed = False
                    error_msg += f"No relations found between {pair}\n"
    return all_checks_passed, error_msg


def test_attribute_vals(soups, all_test_data, tag, id_attr):
    """helper function for checks of values of attributes"""
    all_checks_passed = True
    error_msg = "\n"
    for id in all_test_data:
        soup = soups[id]
        test_data = all_test_data[id]
        timexes = soup.findAll(tag)
        test_data = all_test_data[id]
        for i in test_data:
            attr = test_data[i][0]
            val = test_data[i][1]
            if not timexes[i][attr] == val:
                all_checks_passed = False
                error_msg += f"Expected {timexes[i][id_attr]} to have value {val} of attribute {attr} in text {id}.\n"
    return (all_checks_passed, error_msg)


def test_tag_counts(soups, test_data, tag):
    """helper function for testing counts of different tags"""
    all_checks_passed = True
    error_msg = "\n"
    for id in test_data:
        soup = soups[id]
        tags = soup.findAll(tag)
        if not len(tags) == test_data[id]:
            all_checks_passed = False
            error_msg += f"Expected {test_data[id]} tags, found {len(tags)} in text {id}."
    return all_checks_passed, error_msg


def test_tag_count_matches(soups, tag1, tag2):
    all_checks_passed = True
    error_msg = "\n"
    for id in soups:
        tag1_instances = soups[id].findAll(tag1)
        tag2_instances = soups[id].findAll(tag2)
        if not len(tag1_instances) == len(tag2_instances):
            all_checks_passed = False
            error_msg += f"The text {id} has {len(tag1_instances)} of {tag1} tags and {len(tag2_instances)} of {tag2} tags\n"
    return all_checks_passed, error_msg


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """storing the parsed XML object"""
        os.system('python3 ../nt2tml_v2.py --source="test.jsonl" --output="." --mapping_table="../mapping_table.tsv"')
        cls.ids = ["APW19980227.0494", "APW19980213.1320", "PRI19980205.2000.1998"]
        cls.soups = cls.get_soups(cls.ids)

    @classmethod
    def tearDownClass(cls):
        """removing the created files to make the tests stateless
        
        It is a bad idea to keep files around after the tests are done.
        Because of the statefullness of this, later tests might give incorrect results.
        If you want to look at the files, just do the conversion manually like this:

        python3 ../nt2tml_v2.py --source="test.jsonl" --output="." --mapping_table="../mapping_table.tsv"
        """
        for id in cls.ids:
            os.remove(f"{id}.tml")

    @staticmethod
    def get_soups(ids):
        """is the XML output overall valid (parse-able by BS4)?"""
        # TODO raise an exception if not all ids are found - or should it be a separate test?
        soups = {}
        for id in ids:
            with open(f"{id}.tml", "r") as file:
                content = "".join(file.readlines())
                try:
                    soup = BeautifulSoup(content, features="lxml-xml")
                    soups[id] = soup
                except Exception as e:
                    print("Could not parse the test XML file")
                    print(e)
                    exit(1)
        return soups

    def test_timexes(self):
        """are there as many timexes as in the original TimeML markup?"""
        test_data = {"APW19980227.0494": 11}
        all_checks_passed, error_msg = test_tag_counts(
            self.soups, test_data, tag="TIMEX3"
        )
        assert all_checks_passed, error_msg

    def test_events(self):
        """are there as many events as in the original TimeML markup?"""
        test_data = {"APW19980227.0494": 71}
        all_checks_passed, error_msg = test_tag_counts(self.soups, test_data, tag="EVENT")
        assert all_checks_passed, error_msg

    def test_timex_metadata(self):
        """are the ids and other info for the timexes coming from the timeml metadata?"""
        all_test_data = {"APW19980227.0494": {0: ["functionInDocument", "CREATION_TIME"],
                                              4: ["mod", "EQUAL_OR_MORE"],
                                              10: ["type", "DATE"],
                                              5: ["anchorTimeID", "t142"],
                                              7: ["value", "P4D"]}
                         }
        all_checks_passed, error_msg = test_attribute_vals(soups=self.soups, all_test_data=all_test_data, tag="TIMEX3", id_attr="tid")
        assert all_checks_passed, error_msg

    def test_events_metadata(self):
        """are the ids and other info for the events coming from the timeml metadata?"""
        all_test_data = {"APW19980227.0494": {4:["eid","e8"],
                                              19:["class","OCCURRENCE"],
                                              40:["eid","e72"],
                                              63:["class","I_ACTION"]}
                         }

        all_checks_passed, error_msg = test_attribute_vals(
            soups=self.soups, all_test_data=all_test_data, tag="EVENT", id_attr="eid"
        )
        assert all_checks_passed, error_msg

    def test_instances(self):
        """are there instances for each event?"""
        all_checks_passed, error_msg = test_tag_count_matches(self.soups, "EVENT", "MAKEINSTANCE")
        assert all_checks_passed, error_msg

    def test_self_tlinks(self):
        """are there circular tlinks between event instances?"""
        all_checks_passed = True
        error_msg = "\n"
        for id in self.soups:
            instances = self.soups[id].findAll("MAKEINSTANCE")
            eids = [x["eiid"] for x in instances]
            for eid in eids:
                if self.soups[id].findAll("TLINK", {"eventInstanceID": eid, "relatedToEventInstance": eid}):
                    all_checks_passed = False
                    error_msg += f"found circular TLINK for event {eid} in text {id}\n"
        assert all_checks_passed, error_msg

    # @unittest.skip("Global TLINK coverage test is skipped, because it's too slow")
    def test_tlink_coverage(self):
        """are there tlinks between all event instances?"""
        all_checks_passed = True
        error_msg = "\n"
        for id in self.soups:
            instances = self.soups[id].findAll("MAKEINSTANCE")
            eids = [x["eiid"] for x in instances]
            all_tlinks = [x for x in itertools.combinations(eids, 2)]
            for tlink in all_tlinks:
                a_to_b = {"eventInstanceID": tlink[0], "relatedToEventInstance": tlink[1]}
                b_to_a = {"eventInstanceID": tlink[1], "relatedToEventInstance": tlink[0]}
                if not self.soups[id].findAll("TLINK", a_to_b):
                    if not self.soups[id].findAll("TLINK", b_to_a):
                        all_checks_passed = False
                        error_msg += f"Did not find a TLINK between {tlink[0]} and {tlink[1]} in text {id}\n"
        assert all_checks_passed, error_msg

    # @unittest.skip("Test for uniqueness of TLINKs")
    def test_tlink_uniqueness(self):
        """for any given pair of events, is there only one possible relation label?"""
        all_checks_passed = True
        error_msg = "\n"
        for id in self.soups:
            instances = self.soups[id].findAll("MAKEINSTANCE")
            eids = [x["eiid"] for x in instances]
            all_tlinks = [x for x in itertools.combinations(eids, 2)]
            for tlink in all_tlinks:

                reverse_relations = []
                existing_tlinks = self.soups[id].findAll("TLINK", {"eventInstanceID":tlink[0], "relatedToEventInstance":tlink[1]})
                relations = [x['relType'] for x in existing_tlinks]
                reverse_tlinks  = self.soups[id].findAll("TLINK", {"eventInstanceID":tlink[1], "relatedToEventInstance":tlink[0]})
                reverse_tlinks = [x['relType'] for x in reverse_tlinks]
                # more than one relation in any one direction
                if len(relations) > 1 or len(reverse_relations) > 1:
                    all_checks_passed = False
                    error_msg += f"Too many TLINKs between {tlink[0]} and {tlink[1]} in text {id}: {relations+reverse_relations}\n"
                # superfulous links: symmetrical links (SIMULTANEOUS, MAYBE_SIMULTANEOUS, VAGUE) created in both directions
                elif len({'SIMULTANEOUS', 'MAYBE_SIMULTANEOUS', 'VAGUE'}.intersection(set(relations+reverse_relations))) > 1:
                    all_checks_passed = False
                    error_msg += f"Superfulous symmetrical TLINKs between {tlink[0]} and {tlink[1]} in text {id}: {relations+reverse_relations}\n"
        assert all_checks_passed, error_msg

    @unittest.skip("Test for TLINK coverage")
    def test_timex_tlink_coverage(self):
        """is every event uniquely related to every timex?"""
        all_checks_passed = True
        error_msg = "\n"
        for id in self.soups:
            instances = self.soups[id].findAll("MAKEINSTANCE")
            eids = [x["eiid"] for x in instances]
            timexes = self.soups[id].findAll("TIMEX3")
            tids = [x["tid"] for x in timexes]
            for eid in eids:
                for tid in tids:
                    existing_links = self.soups[id].findAll(
                        "TLINK", {"eventInstanceID": eid, "relatedToTime": tid}
                    ) + self.soups[id].findAll(
                        "TLINK", {"timeID": tid, "relatedToEventInstance": eid}
                    )
                    if len(existing_links) > 1:
                        relations = [x["relType"] for x in existing_links]
                        all_checks_passed = False
                        error_msg += f"Too many TLINKs between {eid} and {tid} in text {id}: {relations}\n"
                    elif len(existing_links) == 0:
                        all_checks_passed = False
                        error_msg += f"No TLINKs found between {eid} and {tid} in text {id}\n"
        assert all_checks_passed, error_msg

    def test_instance_attributes(self):
        """do the instances have the expected TimeML attributes?"""
        all_test_data = {"APW19980227.0494": {"ei2345":["aspect", "PERFECTIVE"],
                                              "ei2340":["modality", "would"],
                                              "ei2342":["polarity", "NEG"],
                                              "ei2368":["tense", "PAST"]}
                         }

        all_checks_passed = True
        error_msg = "\n"
        for id in all_test_data:
            test_data = all_test_data[id]
            for i in test_data:
                attr = test_data[i]
                if not self.soups[id].find("MAKEINSTANCE", {"eiid": i})[attr[0]] == attr[1]:
                    all_checks_passed = False
                    error_msg += f"Expected event {i} to have value {attr[1]} for {attr[0]} attribute in text {id}\n"
        assert all_checks_passed, error_msg

    def test_factuality_instances(self):
        """are there factuality annotations for each instance?"""
        all_checks_passed, error_msg = test_tag_count_matches(self.soups, "FACT_VALUE", "MAKEINSTANCE")
        assert all_checks_passed, error_msg

    def test_factuality(self):
        """do the factuality tags save the right info?"""
        all_test_data = {"APW19980227.0494": {"ei2349":"PS+",
                                              "ei2344":"CT+",
                                              "ei2328":"CT-",
                                              "ei2373":"CT+"}
                         }
        all_checks_passed = True
        error_msg = "\n"
        for id in all_test_data:
            test_data = all_test_data[id]
            for i in test_data:
                fact_value = self.soups[id].find("FACT_VALUE", {"eiid": i})["value"]
                if fact_value != test_data[i]:
                    all_checks_passed = False
                    error_msg += f"Expected event {i} to have factuality {test_data[i]} in text {id}\n"
        assert all_checks_passed, error_msg

    def test_forward_tlinks(self):
        """checking a random set of tlinks that should have BEFORE relation"""
        all_relations = {"APW19980227.0494": {"BEFORE": [("ei2325", "ei2316"),
                                                         ("ei2375", "ei2376"), # e123 e125 - consecutive span
                                                         ("ei2310", "ei2334"), # e8 e55
                                                         ("ei2319", "ei2343"), # e22 e69
                                                         ("ei2326", "ei2359")]} # e43 e98
                         }
        all_checks_passed, error_msg = test_tlinks(all_relations, self.soups, bidirectional=False)
        assert all_checks_passed, error_msg

    @unittest.skip("Depreciated in favor of new conversion rules. Use test_nt2tml_new_rules.py instead")
    def test_simultaneous_tlinks(self):
        """checking a random set of tlinks that should have SIMULTANEOUS or MAYBE_SIMULTANEOUS relation"""
        # ERROR: test_simultaneous_tlinks (__main__.Tests)
        # checking a random set of tlinks that should have SIMULTANEOUS or MAYBE_SIMULTANEOUS relation
        # ----------------------------------------------------------------------
        # Traceback (most recent call last):
        #   File "/Users/vladislavlialin/Documents/nt/utils/test/test_nt2tml.py", line 311, in test_simultaneous_tlinks
        #     all_checks_passed, error_msg = test_tlinks(all_relations, self.soups, bidirectional=True)
        #   File "/Users/vladislavlialin/Documents/nt/utils/test/test_nt2tml.py", line 29, in test_tlinks
        #     relations = all_relations[id]
        # TypeError: tuple indices must be integers or slices, not dict
        all_relations = {"APW19980227.0494": {"SIMULTANEOUS": [("ei2314", "ei2313"), # e12 e15
                                                               ("ei2318", "ei2336"), # e20 e58
                                                               ("ei2345", "ei2346"), # e71 e72
                                                               ("ei2345", "ei2325"), # e71 e41
                                                               ("ei2353", "ei2310"), # e86 e8
                                                               ("ei2361", "ei2365"), # e99 e106 SIMULTANEOUS on centers of partly unbounded events
                                                               ]
                                              },
                         "APW19980213.1310": {"SIMULTANEOUS": [("ei598", "ei600")]}  # e8, e9, [B] with the same timestamp                                              
                         },
        all_checks_passed, error_msg = test_tlinks(all_relations, self.soups, bidirectional=True)
        assert all_checks_passed, error_msg

    def test_vague_tlinks(self):
        """testing INCLUDES relations (directional)"""
        all_relations = {"APW19980227.0494": {"VAGUE": [("ei2326", "ei2357"), # e43, e92
                                                        ("ei2324", "ei2327"), # e37, e44
                                                        ("ei2324", "ei2372"), # e37, e118
                                                        ("ei2353", "ei2358"), # e86, e93
                                                        ("ei2324", "ei2311")] # e37, e10 - parly bounded events with different centers
                                              }
                         }
        all_checks_passed, error_msg = test_tlinks(all_relations, self.soups, bidirectional=True)
        assert all_checks_passed, error_msg

    @unittest.skip("Depreciated in favor of new conversion rules. Use test_nt2tml_new_rules.py instead")
    def test_includes_tlinks(self):
        """testing INCLUDES relations (directional)"""
        # FAIL: test_includes_tlinks (__main__.Tests)
        # testing INCLUDES relations (directional)
        # ----------------------------------------------------------------------
        # Traceback (most recent call last):
        #   File "/Users/vladislavlialin/Documents/nt/utils/test/test_nt2tml.py", line 337, in test_includes_tlinks
        #     assert all_checks_passed, error_msg
        # AssertionError: 
        # No relations found between ('ei2354', 'ei2348')
        # No relations found between ('ei2346', 'ei2329')

        all_relations = {"APW19980227.0494": {"INCLUDES": [("ei2354", "ei2308"), # e87 e3 start of partly bounded event vs [B]
                                                           ("ei2354", "ei2348"), # e87 e75 start of partly bounded event vs [B]
                                                           ("ei2327", "ei2326"), # e44 # e43 permanent vs any bounded event
                                                           ("ei2346", "ei2329"), # e72 e46 permanent and centered unbounded event :(
                                                           ("ei2353", "ei2325"), # e86 e41 interval bounded vs single bounded
                                                           ("ei2327", "ei2326")] # e43, e44 the center of a partly unbounded centered event & bounded event
                                              }
                         }
        all_checks_passed, error_msg = test_tlinks(all_relations, self.soups, bidirectional=False)
        assert all_checks_passed, error_msg

    def test_main2branch_bidirectional(self):
        """checking a random set of bidirectional tlinks between main timeline and branches"""
        all_bidirectional = {'APW19980227.0494': {"SIMULTANEOUS":[("ei2363","ei2345"), # e102, e71 # past branch, permanent event
                                                                  ("ei2366","ei2346")],# e107 e72 future branch + permanent event
                                                  "VAGUE": [("ei2363","ei2325"), # e102, e41 past branch, past event
                                                            ("ei2363", "ei2326"), # e102, e43 #ditto
                                                            ("ei2363", "ei2353"), # e102, ee86 past branch, past bounded event with an interval
                                                            ("ei2363", "ei2357"), # e102, e92 past branch, past partly unbounded event
                                                            ("ei2365", "ei2348"), # e106 e75 future partly bounded + future branch
                                                            ("ei2363", "ei2327")]} # e102, e44 partly unbounded event starting before the attachment point
                             }
        all_checks_passed, error_msg = test_tlinks(all_bidirectional, self.soups, bidirectional=True)
        assert all_checks_passed, error_msg

    def test_main2branch_unidirectional(self):
        """checking a random set of unidirectional tlinks between main timeline and branches"""
        all_unidirectional = {'APW19980227.0494': {"BEFORE":[("ei2363","ei2334"), # e102 e55 past branch + future event
                                                             ("ei2363","ei2369"), # e102, e113 past event + future branch
                                                             ("ei2325", "ei2375"),# e41 e123 past event + future branch
                                                             ("ei2306","ei2366"), # e1 e107 past branch + future branch
                                                             ("ei2358","ei2348"), # e93 e75 past partly bounded + future branch
                                                             ("ei2353","ei2348"), # e86 e75 past interval bounded + future branch
                                                             ("ei2350", "ei2313"), # e82 e12 past branch event to attachment point of the branch
                                                             ("ei2326", "ei2330")]} # e43 e48 future branch event to attachment point of the branch
                              }
        all_checks_passed, error_msg = test_tlinks(all_unidirectional, self.soups, bidirectional=False)
        assert all_checks_passed, error_msg

    def test_branch2branch_unidirectional(self):
        """checking a random set of tlinks between branches"""

        all_unidirectional = {'APW19980227.0494': {"BEFORE":[("ei2363","ei2349"), # e102 e77 # past branch to future branch
                                                             ("ei2363","ei2362")]} # e102 e101
                              }
        all_checks_passed, error_msg = test_tlinks(all_unidirectional, self.soups, bidirectional=False)
        assert all_checks_passed, error_msg

    def test_branch2branch_bidirectional(self):
        """checking a random set of tlinks between branches
        TODO: add a test text with 2+ branches in the same direction, with VAGUE relation between branches"""
        all_unidirectional = {}
        all_checks_passed, error_msg = test_tlinks(
            all_unidirectional, self.soups, bidirectional=True
        )
        assert all_checks_passed, error_msg

    def test_timex_tlinks_bidirectional(self):
        """checking a random set of tlinks to timexes"""

        all_bidirectional = {'APW19980227.0494': {"SIMULTANEOUS":[("ei2309","t154"), # bounded + timex ruled centuries
                                                                  ("ei2306","t2297"), # bounded + timex signed Friday
                                                                  ("ei2350", "t146"), # partly bounded + timex assailed last year
                                                                  ("ei2360", "t151")], #timex at the same point but not in the same span as a bounded event signing Friday
                                                  "VAGUE": [("ei2374", "t143"), #past branch event without timex to past main timeline timex planned+last May
                                                            ("ei2363", "t143")]} # could be TIMEX_INFERENCE: past branch event with timex to timex of a main branch event (fell last year > last May
                             }

        all_checks_passed, error_msg = test_tlinks(
            all_bidirectional, self.soups, bidirectional=True, timex=True
        )
        assert all_checks_passed, error_msg

    def test_timex_tlinks_unidirectional(self):
        """checking a random set of bidirectional tlinks to timexes"""
        # TODO Add a text with timexes on branches and write tests for that
        all_unidirectional = { "APW19980227.0494": {"BEFORE": [("ei2310", "t152"),  # standalone timex span breakup 1996
                                                               ("ei2310", "t142"),  # timex from a bounded event span breakup 02/27/1998
                                                               ("ei2363", "t2297")]}  # past branch to future timex Friday
        }

        all_checks_passed, error_msg = test_tlinks(
            all_unidirectional, self.soups, bidirectional=False, timex=True
        )
        assert all_checks_passed, error_msg

    @unittest.skip("Depreciated in favor of new conversion rules. Use test_nt2tml_new_rules.py instead")
    def test_partially_unbounded_with_vague_end_includes(self):
        """checking a random set of tlinks between partially unbounded events with vague end

        Note: test.jsonl doesn't have any of these, so we are using a different test file.
        These are annotations from tbd_a1.jsonl
        """
        # FAIL: test_partially_unbounded_with_vague_end_includes (__main__.Tests)
        # checking a random set of tlinks between partially unbounded events with vague end
        # ----------------------------------------------------------------------
        # Traceback (most recent call last):
        #   File "/Users/vladislavlialin/Documents/nt/utils/test/test_nt2tml.py", line 439, in test_partially_unbounded_with_vague_end_includes
        #     assert all_checks_passed, error_msg
        # AssertionError: 
        # No relations found between ('ei102', 'ei91')
        # No relations found between ('ei102', 'ei95')

        # APW19980213.1320
        # type:3 is [U}
        # event index: 4 event: {'span': [68, 73], 'type': 3, 'time': '1:2', 'relto': '', 'factuality': ''} event text: the crippling Asian financial crisis . -> eid=3, eiid=ei91
        # event index: 8 event: {'span': [100, 104], 'type': 3, 'time': '1:2', 'relto': '', 'factuality': ''} event text: the Asian economic crisis . -- ei7
        # <event id="14" type={U} tml=: relto= speech=> business and tourism ties with </event> -- ei102 -- 14 INCLUDES 4 and 8

        all_unidirectional = {
            "APW19980213.1320": {
                "INCLUDES": [
                    ("ei102", "ei91"),  # {:} INCLUDES [1:2}
                    ("ei102", "ei95"),  # {:} INCLUDES [1:2}
                ],
            }
        }

        all_checks_passed, error_msg = test_tlinks(
            all_unidirectional, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg

    def test_partially_unbounded_with_vague_end_overlap(self):
        # <event id="7" type=[B] tml=0:2 relto= speech=> of services between Australia, Indonesia, Thailand and </event> -- ei94-- INCLUDES
        relations = {
            "APW19980213.1320": {
                "OVERLAP": [
                    ("ei91", "ei94"),  # [1:2} OVERLAP [0:2]
                    ("ei95", "ei94"),  # [1:2} OVERLAP [0:2]
                ],
            }
        }

        all_checks_passed, error_msg = test_tlinks(
            relations, self.soups, bidirectional=True
        )
        assert all_checks_passed, error_msg

    def test_partially_unbounded_with_vague_end_before(self):
        # PRI19980205.2000.1998
        # event index: 2 event: {'span': [20, 28], 'type': 3, 'time': '0.5:5', 'relto': '', 'factuality': ''} event text: against the high level of unemployment in the country. -- eiid=ei72
        # event index: 7 event: {'span': [74, 82], 'type': 3, 'time': '3:5', 'relto': '', 'factuality': ''} event text: Joblessness is now at its highest level in Germany  -- eiid=ei79

        # eid=ei80, BEFORE, <event id="8" type=[B] tml=0 relto= speech=> since the second world </event> war .

        all_unidirectional = {
            "PRI19980205.2000.1998": {
                "BEFORE": [
                    ("ei80", "ei72"),
                    ("ei80", "ei79"),
                ],
            }
        }

        all_checks_passed, error_msg = test_tlinks(
            all_unidirectional, self.soups, bidirectional=False
        )
        assert all_checks_passed, error_msg


if __name__ == "__main__":
    unittest.main()
