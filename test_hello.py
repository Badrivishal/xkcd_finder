import unittest

class TestHello(unittest.TestCase):
    def test_hello(self):
        self.assertFalse(True)


def hello():
    return "Hello, World!"

if __name__ == "__main__":
    unittest.main()