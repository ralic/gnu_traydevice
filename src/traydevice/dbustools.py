# -*- coding: utf-8 -*-
from dbus import Interface
from dbus import Boolean
from logging import getLogger

#TODO: dbus-standard-interfaces-wrappers might be standalone framework on it's own, if properly implemented 
def dbus_to_string(dbus_bytearray):
	if not dbus_bytearray:
		return None
	utf8String = dbus_bytearray.decode('utf-8')
	utf8String = utf8String.replace('\0', '')
	return utf8String;

def dbus_to_bool(dbus_boolean):
	if dbus_boolean:
		return True
	else:
		return False

def dbus_to_list(dbus_list):
	array=[]
	for e in dbus_list:
		array.append(dbus_to_object(e))
	return array

def dbus_to_object(dbus_object):
	getLogger(__name__).debug('Parsing:%s(%s)'%(dbus_object, type(dbus_object)))
	if isinstance(dbus_object, Boolean):
		return dbus_to_bool(dbus_object)
	if isinstance(dbus_object, list):
		return dbus_to_list(dbus_object)
	return dbus_to_string(dbus_object)

class DBusInterfaceWrapper:
	"""
		This has to be overriden
	"""
	DBUS_API_NAME=None
	
	def __init__(self, dbus_proxy_object):
		self.proxy = dbus_proxy_object
		self.dbus_interface = Interface(dbus_proxy_object, self.DBUS_API_NAME)

class org_freedesktop_DBus_Properties(DBusInterfaceWrapper):
	"""
		Class representing org.freedesktop.DBus.Properties as defined at http://dbus.freedesktop.org/doc/dbus-specification.html#standard-interfaces-properties
	"""
	DBUS_API_NAME='org.freedesktop.DBus.Properties'
	byte_arrays=True
	def __init__(self, dbus_proxy_object):
		DBusInterfaceWrapper.__init__(self, dbus_proxy_object);
	"""
    org.freedesktop.DBus.Properties.Get (in STRING interface_name,
                                         in STRING property_name,
                                         out VARIANT value);
	"""		
	def Get(self, interface_name, property_name):
		return self.dbus_interface.Get(interface_name, property_name,byte_arrays=self.byte_arrays)

	"""
    org.freedesktop.DBus.Properties.Set (in STRING interface_name,
                                         in STRING property_name,
                                         in VARIANT value);
	"""
	def Set(self, interface_name, property_name, value):
		return self.dbus_interface.Set(interface_name, property_name, value)
	"""
    org.freedesktop.DBus.Properties.GetAll (in STRING interface_name,
                                            out DICT<STRING,VARIANT> props);
	"""	
	def GetAll(self, interface_name):
		return self.dbus_interface.GetAll(interface_name,byte_arrays=self.byte_arrays)

	"""	        
	If one or more properties change on an object, the org.freedesktop.DBus.Properties.PropertiesChanged signal may be emitted (this signal was added in 0.14):
	
	              org.freedesktop.DBus.Properties.PropertiesChanged (STRING interface_name,
	                                                                 DICT<STRING,VARIANT> changed_properties,
	                                                                 ARRAY<STRING> invalidated_properties);
	"""
	pass

class org_freedesktop_DBus_ObjectManager(DBusInterfaceWrapper):
	DBUS_API_NAME='org.freedesktop.DBus.ObjectManager'
	byte_arrays=True
	def __init__(self, dbus_proxy_object):
		DBusInterfaceWrapper.__init__(self, dbus_proxy_object);
	
	"""
		org.freedesktop.DBus.ObjectManager.GetManagedObjects (out DICT<OBJPATH,DICT<STRING,DICT<STRING,VARIANT>>> objpath_interfaces_and_properties);
	"""
	def GetManagedObjects(self):
		return self.dbus_interface.GetManagedObjects(byte_arrays=self.byte_arrays)
	
	"""
		signal_handler is a method implementing this signature:
		org.freedesktop.DBus.ObjectManager.InterfacesAdded (OBJPATH object_path,
																											DICT<STRING,DICT<STRING,VARIANT>> interfaces_and_properties);
	"""
	def connect_to_InterfacesAdded(self, signal_handler_method):
		self.dbus_interface.connect_to_signal('InterfacesAdded', signal_handler_method, byte_arrays=self.byte_arrays)
	
	"""
		signal_handler is a method implementing this signature:
		org.freedesktop.DBus.ObjectManager.InterfacesRemoved (OBJPATH object_path,
																																ARRAY<STRING> interfaces);
	"""
	def connect_to_InterfacesRemoved(self, signal_handler_method):
		self.dbus_interface.connect_to_signal('InterfacesRemoved', signal_handler_method, byte_arrays=self.byte_arrays)
		

class org_freedesktop_DBus_Introspectable(DBusInterfaceWrapper):
	DBUS_API_NAME='org.freedesktop.DBus.Introspectable'
	byte_arrays=True
	def __init__(self, dbus_proxy_object):
		DBusInterfaceWrapper.__init__(self, dbus_proxy_object);
	
	"""
		org.freedesktop.DBus.Introspectable.Introspect (out STRING xml_data)
	"""
	def Introspect(self):
		return self.dbus_interface.Introspect()
	
	"""
		Fetch dictionary(interface_name, list of property names available for interface)
	"""
	def get_interface_properties(self, introspection_data):
		from lxml import etree
		parsed = etree.fromstring(introspection_data)
		result = dict()
		for interface_name in parsed.xpath('//interface/@name'):
			getLogger(__name__).debug("Analysing '%s'"%interface_name)
			result[interface_name]=parsed.xpath("//interface[@name='%s']/property/@name"%interface_name)
		return result
		
		
	