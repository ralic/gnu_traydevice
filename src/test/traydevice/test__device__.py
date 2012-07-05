from unittest import TestCase
from unittest import main

import device
from device import PropertyAccessor, PropertyResolver

class test_parse_key(TestCase):

    def test_empty_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([], tested.parse_key(''))

    def test_simple_unqualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([(None,'IdLabel')], tested.parse_key('IdLabel'))

    def test_simple_qualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([('org.freedesktop.UDisks2.Block','IdLabel')], tested.parse_key('org.freedesktop.UDisks2.Block.IdLabel'))

    def test_nested_unqualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([(None,'Drive'),(None,'Media'),], tested.parse_key('Drive/Media'))

    def test_nested_qualified_key(self):
      tested = device.PropertyAccessor(None, None, None)
      self.assertEqual([('org.freedesktop.UDisks2.Block','Drive')
                       ,('org.freedesktop.UDisks2.Drive','Media'),]
                       , tested.parse_key('org.freedesktop.UDisks2.Block.Drive/org.freedesktop.UDisks2.Drive.Media'))


class test_PropertyResolver(TestCase):
  class MockAccessor:
    
    def get_property(self, name):
      if name=="Drive/Optical":
        return 'true'
      if name=="Drive/Media":
        return "optical_cd"
      raise "Unmocked key %s"%name

  def test_xml_comments(self):
    resolver = PropertyResolver(test_PropertyResolver.MockAccessor())
    test_xml = """
      <and>
        <match key="Drive/Optical" bool="true"/>
        <match key="Drive/Media" regex="optical_.*"/><!-- see http://people.freedesktop.org/~david/udisks2-20111102/gdbus-org.freedesktop.UDisks2.Drive.html#gdbus-property-org-freedesktop-UDisks2-Drive.Media -->
      </and>
    """
    
    from lxml import etree
    condition = etree.fromstring(test_xml) 
    
    comments_out = filter(resolver.is_not_ignored_tag, condition)
    self.assertEquals(2, len(comments_out))
    
if __name__=='__main__':
    main()    