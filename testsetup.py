from unittest import TestCase
from unittest import main

import setup


class test_cut_prefix(TestCase):
    def test_prefix_equals_pathname(self):
        self.assertEqual('.', setup.cut_prefix('/usr','/usr'))
    def test_prefix_slash_path_no_slash(self):
        self.assertEqual('.', setup.cut_prefix('/usr','usr'))


if __name__=='__main__':
    main()    
