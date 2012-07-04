from unittest import TestCase
from unittest import main

import device

class test_parse_key(TestCase):
  
    def test_empty_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([], tested.parse_key(''))

    def test_simple_unqualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([(None,'IdLabel')], tested.parse_key('IdLabel'))

    def test_simple_qualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([('org.freedesktop.UDisks2.Block','IdLabel')], tested.parse_key('(org.freedesktop.UDisks2.Block)IdLabel'))

    def test_nested_unqualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([(None,'Drive'),(None,'Media'),], tested.parse_key('Drive/Media'))

    def test_nested_qualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([('org.freedesktop.UDisks2.Block','Drive')
                       ,('org.freedesktop.UDisks2.Drive','Media'),]
                       , tested.parse_key('(org.freedesktop.UDisks2.Block)Drive/(org.freedesktop.UDisks2.Drive)Media'))
         

if __name__=='__main__':
    main()    