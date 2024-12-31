import serial
import dlt645
import logging
from dlt645.constants import *

logging.basicConfig(level=logging.DEBUG)

ser = serial.Serial(
    port="COM10",
    baudrate=115200,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=2
)

read_control = {
    "direction": MAIN,
    "response": RESPONSE_CORRECT,
    "more": NO_MORE_DATA,
    "function": FUNCTION_CODES[DLT645_1997]["READ_DATA"],
}

write_control = {
    "direction": MAIN,
    "response": RESPONSE_CORRECT,
    "more": NO_MORE_DATA,
    "function": FUNCTION_CODES[DLT645_1997]["WRITE_DATA"],  # Write function code
}

def get_meter_data(addr1, addr2):
    # Initialize variables to store the results for each register
    reg1_value = None
    reg2_value = None
    # List of addresses to query
    addresses = [addr1, addr2]
    # dictionary to map address pairs to (msb, lsb) values
    address_map = {
        (0x00D9, 0x00E9): (0.01, 0.01),  # Voltage A
        (0x00DA, 0x00EA): (0.01, 0.01),  # Voltage B
        (0x00DB, 0x00EB): (0.01, 0.01),  # Voltage C
        (0x00DD, 0x00ED): (0.001, 0.001),  # Current A
        (0x00DE, 0x00EE): (0.001, 0.001),  # Current B
        (0x00DF, 0x00EF): (0.001, 0.001),  # Current C
        (0x00B0, 0x00C0): (4, 4),  # Pmean(W) Total
        (0x00B1, 0x00C1): (1, 1),  # Pmean(W) A
        (0x00B2, 0x00C2): (1, 1),  # Pmean(W) B
        (0x00B3, 0x00C3): (1, 1),  # Pmean(W) C
        (0x00B4, 0x00C4): (4, 4),  # Qmean(VAr) Total
        (0x00B5, 0x00C5): (1, 1),  # Qmean(VAr) A
        (0x00B6, 0x00C6): (1, 1),  # Qmean(VAr) B
        (0x00B7, 0x00C7): (1, 1),  # Qmean(VAr) C
        (0x00B8, 0x00C8): (4, 4),  # Smean(VA) Total
        (0x00B9, 0x00C9): (1, 1),  # Smean(VA) A
        (0x00BA, 0x00CA): (1, 1),  # Smean(VA) B
        (0x00BB, 0x00CB): (1, 1),  # Smean(VA) C
        (0x00D0, 0x00E0): (4, 4),  # PmeanF(W) Total
        (0x00D1, 0x00E1): (1, 1),  # PmeanF(W) A
        (0x00D2, 0x00E2): (1, 1),  # PmeanF(W) B
        (0x00D3, 0x00E3): (1, 1),  # PmeanF(W) C
        (0x00D4, 0x00E4): (4, 4),  # PmeanH(W) Total
        (0x00D5, 0x00E5): (1, 1),  # PmeanH(W) A
        (0x00D6, 0x00E6): (1, 1),  # PmeanH(W) B
        (0x00D7, 0x00E7): (1, 1),  # PmeanH(W) C
    }

    # Use the dictionary to look up msb, lsb values based on the address pair
    msb, lsb = address_map[(addr1, addr2)]  # No default, will raise error if not found

    for i, addr in enumerate(addresses):
        addr += 0xD000  # Add 0xD000 to address (as per your original logic)
        print(f"Querying address {i + 1}: {hex(addr)}")

        # Prepare the frame
        frame = dlt645.Frame(addr=station_addr, control=read_control)
        frame.data = '%04X' % addr
        print("Sent frame:     ",frame.dump().hex())

        # Send the frame
        dlt645.write_frame(ser, frame=frame, awaken=True)

        # Read the response
        frame_data = dlt645.read_frame(dlt645.iogen(ser))

        # Debug: print the received frame
        print("Received frame: ", frame_data.dump().hex())
        print(frame_data.data[0:4],end='\n')

        # Store the received data in separate variables
        if len(frame_data.data) >= 4:
            if i == 0:
                reg1_value = int(frame_data.data[0:4], 16)
            elif i == 1:
                reg2_value = int(frame_data.data[0:4], 16)
        else:
            print(f"Error: Incomplete data received for address {hex(addr)}")
            continue

        # Perform conversion logic here using reg1_value and reg2_value for V,A,W,VAr,VA,Fundamental&Harmonic for W
        if reg1_value is not None and reg2_value is not None:
            reg2_value = (reg2_value >> 8) & 0xFF  # Shift right by 8 and mask with 0xFF bcoz we need only higher 8 bits
            result = (reg1_value * msb) + (reg2_value * lsb / 256)
            print(f"Result of conversion : {float(result)}\n")
            return result
        else:
            print("warning: One or more registers did not return valid data to perform conversion.")

def get_meter_data1(addr):
    valid_addrs = addr
    addr += 0xD000  # Add 0xD000 to address (as per your original logic)
    print(f"Querying address: {hex(addr)}")
    # Prepare the frame
    frame = dlt645.Frame(addr=station_addr, control=read_control)
    frame.data = '%04X' % addr
    print("Sent frame:     ", frame.dump().hex())
    # Send the frame
    dlt645.write_frame(ser, frame=frame, awaken=True)
    # Read the response
    frame_data = dlt645.read_frame(dlt645.iogen(ser))
    # Debug: print the received frame
    print("Received frame: ", frame_data.dump().hex())
    print(frame_data.data[0:4], end='\n')

    reg1_value = int(frame_data.data[0:4], 16)
    valid_addresses = (0x00BC, 0x00BD, 0x00BE, 0x00BF, 0x00F9, 0x00FA, 0x00FB, 0x00F8)
    if valid_addrs in valid_addresses:
            # Select the msb multiplier based on the address
        if addr in (0xD0BC, 0xD0BD, 0xD0BE, 0xD0BF):
            msb = 0.001
        elif addr in (0xD0F9, 0xD0FA, 0xD0FB):
            msb = 0.1
        else:
            msb = 0.01  # Default case, could be unnecessary given valid_addresses

            # Ensure reg1_value is not None and perform calculation
        if reg1_value is not None:
            result = reg1_value * msb
            print(f"Result of conversion: {float(result)}\n")
        else:
            print(f"Address {hex(addr)} is not valid for conversion.")
    else:
            # No calculation for invalid addresses
            print(int(frame_data.data[0:4], 16))
            print()
            return reg1_value

def write_meter_data(addr, data_value):
    addr += 0xD000  # Add 0xD000 to address (as per your original logic)
    print(f"Querying address: {hex(addr)}")
    if isinstance(data_value, int):
        data_value = format(data_value, 'X')  # Convert integer to uppercase hex string (without '0x' prefix)
    int_value = int(data_value, 16)
    #print(f"Converted integer value: {int_value}")

    data_value = list(int_value.to_bytes(2, 'big'))
    data_value += [0x11, 0x11, 0x11, 0x01]

    addr_bytes = addr.to_bytes(2, 'big')

    frame_data = bytes(data_value) + addr_bytes

    frame = dlt645.Frame(addr=station_addr, control=write_control)
    frame.data = frame_data

    # Print the frame for debugging
    print(f"Sent frame: {frame.dump().hex()}")

    # Send the frame
    dlt645.write_frame(ser, frame=frame, awaken=True)

    # Read the response
    frame_data_received = dlt645.read_frame(dlt645.iogen(ser))
    print("Received frame :", frame_data_received.dump().hex(),"\n")

def calibrate_vol_cur(addr1,addr2,gain_addr):

    valid_vol_addresses = (0x00D9, 0x00E9, 0x00DA, 0x00EA, 0x00DB, 0x00EB)
    valid_cur_addresses = (0x00DD, 0x00ED, 0x00DE, 0x00EE, 0x00DF, 0x00EF)

    vol_cur_gain = get_meter_data1(gain_addr)

    if addr1 and addr2 in valid_vol_addresses:
        ref_value = 220
        if vol_cur_gain == 0:
            const_vol_cur_gain = 52800
        else:
            const_vol_cur_gain = vol_cur_gain

    elif addr1 and addr2 in valid_cur_addresses:
        ref_value = 3.0
        if vol_cur_gain == 0:
            const_vol_cur_gain = 30000
        else:
            const_vol_cur_gain = vol_cur_gain

    else:
        print("No valid adrresses",'\n')

    vol_cur_measured_value = get_meter_data(addr1, addr2)

    new_vol_cur_gain = ((ref_value/vol_cur_measured_value)*const_vol_cur_gain)
    print(f"vol_cur gain :{float(new_vol_cur_gain)}")

    rounded_vol_cur_gain = round(new_vol_cur_gain)  # Round to the nearest integer
    hex_rep = '0x'+ format(rounded_vol_cur_gain, '04X')
    print(f"vol_cur gain (hex) : {hex_rep}",'\n')

    write_meter_data(gain_addr, hex_rep)
    get_meter_data(addr1, addr2)

# Get station address (you may already have this function implemented elsewhere)
station_addr = dlt645.get_addr(ser)
print(f"Station Address: {station_addr}")

# Example usage:

#get_meter_data(0x00D9, 0x00E9)
#get_meter_data1(0x0061)
#write_meter_data(0x0069, 0x8000)
#get_meter_data1(0x0065)
# calibrate_vol_cur(0x00D9, 0x00E9, 0x0061)
# calibrate_vol_cur(0x00DA, 0x00EA, 0x0065)
# calibrate_vol_cur(0x00DB, 0x00EB, 0x0069)
get_meter_data(0x00D9, 0x00E9)
get_meter_data(0x00DA, 0x00EA)
get_meter_data(0x00DB, 0x00EB)

#get_meter_data1(0x00ed)
# write_meter_data(0x0062, 0x8000)
# write_meter_data(0x0066, 0x8000)
# write_meter_data(0x006A, 0x8000)
# calibrate_vol_cur(0x00DD, 0x00ED, 0x0062)
# calibrate_vol_cur(0x00DE, 0x00EE, 0x0066)
# calibrate_vol_cur(0x00DF, 0x00EF, 0x006A)
get_meter_data(0x00DD, 0x00ED)
get_meter_data(0x00DE, 0x00EE)
get_meter_data(0x00DF, 0x00EF)