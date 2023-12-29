# Converting the hexadecimal string to bytes
hex_string = "050014000a000f00050014000a000f00050014000a000f00050014000a000f00050014000a000f00050014000a000f00666654429a990d41"
byte_data = bytes.fromhex(hex_string)

# Calculating the size of the byte data
payload_size = len(byte_data)
print(payload_size)