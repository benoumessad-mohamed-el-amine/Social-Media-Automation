import unittest
from src.cogs.hello import HelloCog

class TestHelloCog(unittest.TestCase):
    def setUp(self):
        self.cog = HelloCog()

    def test_hello_command(self):
        response = self.cog.hello()
        self.assertEqual(response, "Hello, World!")

if __name__ == '__main__':
    unittest.main()