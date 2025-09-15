import unittest

from app import get_id_from_string

class TestGetIdFromString(unittest.TestCase):
    def test_get_id_from_string(self):
        test_string = """
    [844] https://xkcd.com/844/

    This comic fits best because it directly addresses the topic of programmers debugging code, specifically the challenges and frustrations that come with it. The comic's flowchart and accompanying text poke fun at the common experience of programmers struggling to write good code, and the inevitable cycle of rewriting and restarting that often ensues.
    """
        self.assertEqual(get_id_from_string(test_string), "844")

if __name__ == "__main__":
    unittest.main()