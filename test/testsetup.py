from unittest import TestCase
from unittest import main


class test_cut_prefix(TestCase):
    def test_prefix_equals_pathname(self):
        self.assertEqual('.', setup.cut_prefix('/usr','/usr'))
    def test_prefix_slash_path_no_slash(self):
        self.assertEqual('.', setup.cut_prefix('/usr','usr'))


if __name__=='__main__':
    import os,sys,inspect
    cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
    setup_folder = os.path.abspath('%s/..'%cmd_folder)
    if setup_folder not in sys.path:
        sys.path.insert(0, setup_folder)
    import setup
    main()    
