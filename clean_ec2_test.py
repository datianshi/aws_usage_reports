import unittest
import clean_ec2


class TestCleanEC2(unittest.TestCase):

    def setUp(self):
        pass

    def test_valid_true_tag(self):
        instance = {
            'Tags': [
                {
                    'Key': 'do_not_delete',
                    'Value': 'true'
                }
            ]
        }
        self.assertTrue(clean_ec2.do_not_delete(instance))

    def test_empty_tag(self):
        instance = {
            'Tags': [
            ]
        }
        self.assertFalse(clean_ec2.do_not_delete(instance))

    def test_no_tag(self):
        instance = {
        }
        self.assertFalse(clean_ec2.do_not_delete(instance))


    def test_no_do_not_delete_tag(self):
        instance = {
            'Tags': [
                {
                    'Name': 'test',
                    'Value': 'test'
                }
            ]
        }
        self.assertFalse(clean_ec2.do_not_delete(instance))
