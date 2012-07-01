def dbus_to_string(dbus_bytearray):
	if not dbus_bytearray:
		return None
	utf8String = dbus_bytearray.decode('utf-8')
	utf8String = utf8String.replace('\0', '')
	return utf8String;