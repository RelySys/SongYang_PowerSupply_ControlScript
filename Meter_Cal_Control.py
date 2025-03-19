import serial
import dlt645
import logging
import math
import time 
import os
import json
from dlt645.constants import *

valid_vol_addresses = (0x00D9, 0x00E9, 0x00DA, 0x00EA, 0x00DB, 0x00EB)
valid_cur_addresses = (0x00DD, 0x00ED, 0x00DE, 0x00EE, 0x00DF, 0x00EF)
valid_pwr_addresses = (0x00B1, 0x00C1, 0x00B2, 0x00C2, 0x00B3, 0x00C3)

logging.basicConfig(level=logging.DEBUG)

class MeterCalControl:
    def __init__(self,port, baudrate):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=2
        )
        # Get station address (you may already have this function implemented elsewhere)
        self.station_addr = dlt645.get_addr(self.ser)
        print(f"Station Address: {self.station_addr}")

        self.read_control = {
            "direction": MAIN,
            "response": RESPONSE_CORRECT,
            "more": NO_MORE_DATA,
            "function": FUNCTION_CODES[DLT645_1997]["READ_DATA"],
        }

        self.write_control = {
            "direction": MAIN,
            "response": RESPONSE_CORRECT,
            "more": NO_MORE_DATA,
            "function": FUNCTION_CODES[DLT645_1997]["WRITE_DATA"],  # Write function code
        }

    def dec2hex_64bit(self,n):
        # Convert to 64-bit signed integer (2's complement)
        if n < 0:
            # Apply two's complement for negative numbers
            n = (1 << 64) + n  # Add 2^64 to the negative number

        # Mask the result to get only the last 2 bytes (16 bits)
        last_2_bytes = n & 0xFFFF  # 0xFFFF is a mask for the last 2 bytes (16 bits)

        # Convert to hexadecimal and format as 4 digits (2 bytes = 4 hex digits)
        hex_value = format(last_2_bytes, '04X')  # Pad with leading zeros if needed

        return hex_value

    def get_meter_data(self,addr1, addr2):
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
            if addr == 0x0070:
                addr += 0xE000
            else:
                addr += 0xD000  # Add 0xD000 to address (as per your original logic)
                #print(f"Querying address {i + 1}: {hex(addr)}")

            # Prepare the frame
            frame = dlt645.Frame(addr=self.station_addr, control=self.read_control)
            frame.data = '%04X' % addr
            #print("Sent frame:     ",frame.dump().hex())

            # Send the frame
            dlt645.write_frame(self.ser, frame=frame, awaken=True)

            # Read the response
            frame_data = dlt645.read_frame(dlt645.iogen(self.ser))

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
                reg2_value = (reg2_value >> 8) & 0xFF  # Shift right by 8 and mask with 0xFF because we need only higher 8 bits
                result = (reg1_value * msb) + (reg2_value * lsb / 256)
                if addr1 and addr2 in valid_vol_addresses:
                    if addr1 == 0x00D9:
                        print(f"voltage R Phase: {float(result)}")
                    elif addr1 == 0x00DA:
                        print(f"voltage Y Phase: {float(result)}") 
                    elif addr1 == 0x00DB:
                        print(f"voltage B Phase: {float(result)}")
                elif addr1 and addr2 in valid_cur_addresses:
                    if addr1 == 0x00DD:
                        print(f"Current R Phase: {float(result)}")
                    elif addr1 == 0x00DE:
                        print(f"Current Y Phase: {float(result)}") 
                    elif addr1 == 0x00DF:
                        print(f"Current B Phase: {float(result)}")
                elif addr1 and addr2 in valid_pwr_addresses:
                    if addr1 == 0x00B1:
                        print(f"Power R Phase: {float(result)}")
                    elif addr1 == 0x00B2:
                        print(f"Power Y Phase: {float(result)}") 
                    elif addr1 == 0x00B3:
                        print(f"Power B Phase: {float(result)}")

                return result
            #else:
                #print("warning: One or more registers did not return valid data to perform conversion.")
                #print()

    def get_meter_data1(self,addr):
        valid_addrs = addr
        if addr == 0x0070:
            addr += 0xE000
        else:
            addr += 0xD000  # Add 0xD000 to address (as per your original logic)
        # print(f"Querying address: {hex(addr)}")
        # Prepare the frame
        frame = dlt645.Frame(addr=self.station_addr, control=self.read_control)
        frame.data = '%04X' % addr
        #print("Sent frame:     ", frame.dump().hex())
        # Send the frame
        dlt645.write_frame(self.ser, frame=frame, awaken=True)
        # Read the response
        frame_data = dlt645.read_frame(dlt645.iogen(self.ser))
        # Debug: print the received frame

        print("Received frame: ", frame_data.dump().hex())
        # print(frame_data.data[0:4], end='\n')
        if(valid_addrs == 0x0061):
            print("Voltage Gain R_phase: ", frame_data.data[0:4], end='\n')
        elif(valid_addrs == 0x0065):
            print("Voltage Gain Y_phase: ", frame_data.data[0:4], end='\n')
        elif(valid_addrs == 0x0069):
            print("Voltage Gain B_phase: ", frame_data.data[0:4], end='\n')
        elif(valid_addrs == 0x0062):
            print("Current Gain R_phase: ", frame_data.data[0:4], end='\n')
        elif(valid_addrs == 0x0066):
            print("Current Gain Y_phase: ", frame_data.data[0:4], end='\n')
        elif(valid_addrs == 0x006A):
            print("Current Gain B_phase: ", frame_data.data[0:4], end='\n')

        reg1_value = int(frame_data.data[0:4], 16)

        valid_addresses = (0x00BC, 0x00BD, 0x00BE, 0x00BF, 0x00F9, 0x00FA, 0x00FB, 0x00F8)
        if valid_addrs in valid_addresses:
                # Select the msb multiplier based on the address
            if addr in (0xD0BC, 0xD0BD, 0xD0BE, 0xD0BF):
                msb = 0.001
            elif addr in (0xD0F9, 0xD0FA, 0xD0FB):
                msb = 0.1
                name = "phase angle"
            else:
                msb = 0.01  # Default case, could be unnecessary given valid_addresses
                name = "freq"

                # Ensure reg1_value is not None and perform calculation
            if reg1_value is not None:
                result = reg1_value * msb
                print(f"{name}: {float(result)}\n")
                return result

            else:
                print(f"Address {hex(addr)} is not valid for conversion.")
        else:
                # No calculation for invalid addresses
                # print(int(frame_data.data[0:4], 16))
                print()
                return reg1_value

    def write_meter_data(self,addr, data_value):
        if addr == 0x0070:
            addr += 0xE000
        else:
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
        frame = dlt645.Frame(addr=self.station_addr, control=self.write_control)
        frame.data = frame_data
        # Print the frame for debugging
        #print(f"Sent frame: {frame.dump().hex()}")
        # Send the frame
        dlt645.write_frame(self.ser, frame=frame, awaken=True)
        # Read the response
        frame_data_received = dlt645.read_frame(dlt645.iogen(self.ser))
        #print("Received frame :", frame_data_received.dump().hex(),"\n")
        #print("write completed")

    def calibrate_vol_cur(self,addr1,addr2,gain_addr,ref_value):
        const_vol_cur_gain = 0
        # valid_vol_addresses = (0x00D9, 0x00E9, 0x00DA, 0x00EA, 0x00DB, 0x00EB)
        # valid_cur_addresses = (0x00DD, 0x00ED, 0x00DE, 0x00EE, 0x00DF, 0x00EF)

        vol_cur_gain = self.get_meter_data1(gain_addr)
        print("vol_cur_gain",{hex(vol_cur_gain)})

        if addr1 and addr2 in valid_vol_addresses:
            #ref_value = 220
            if vol_cur_gain == 0:
                const_vol_cur_gain = 52800
            else:
                const_vol_cur_gain = vol_cur_gain

        elif addr1 and addr2 in valid_cur_addresses:
            #ref_value = 3.0
            if vol_cur_gain == 0:
                const_vol_cur_gain = 30000
            else:
                const_vol_cur_gain = vol_cur_gain

        else:
            print("No valid addresses",'\n')

        vol_cur_measured_value = self.get_meter_data(addr1, addr2)
        print("vol_cur_measured_value",vol_cur_measured_value)

        new_vol_cur_gain = ((ref_value/vol_cur_measured_value)*const_vol_cur_gain)
        print(f"new_vol_cur_gain :{float(new_vol_cur_gain)}")

        rounded_vol_cur_gain = round(new_vol_cur_gain)  # Round to the nearest integer
        hex_rep = '0x'+ format(rounded_vol_cur_gain, '04X')
        print(f"new_vol_cur_gain (hex) : {hex_rep}",'\n')

        self.write_meter_data(gain_addr, hex_rep)
        self.get_meter_data(addr1, addr2)
    
    def calibrate_power(self,gain_addr):
        if gain_addr == 0x0047:
            addr1,addr2 = 0x00B1,0x00C1
        elif gain_addr == 0x0049:
            addr1,addr2 = 0x00B2,0x00C2
        elif gain_addr == 0x004B:
            addr1,addr2 = 0x00B3,0x00C3
        else:
            print("no valid register")
            return

        # meter_control.write_meter_data(gain_addr, 0x0000)
        # measured_power = self.get_meter_data(addr1, addr2)
        total_angle = 0  # Initialize a variable to accumulate the sum of the results
        for i in range(10):  # Run the loop 10 times, and use i as the loop variable
            measured_angle = self.get_meter_data(addr1, addr2)
            time.sleep(0.5)
            total_angle += measured_angle  # Add the result to the total
        # Now, calculate the average using the number of iterations
        average_angle = (total_angle / 10)

        error = ((average_angle-660)/660)
        print(error)
        error1 = (-error/(1+error))
        print(error1)

        new_power_gain = (error1*32768)
        print(f"new_power_gain :{float(new_power_gain)}")

        rounded_power_gain = round(new_power_gain)  # Round to the nearest integer
        print(f"rounded_power_gain :", rounded_power_gain)

        hex_rep = self.dec2hex_64bit(rounded_power_gain)
        print(f"new_power_gain (hex) : {hex_rep}", '\n')

        self.write_meter_data(gain_addr, hex_rep)
 
    def calibrate_phaseangle(self, gain_addr):
        g_phase: float = 3763.739

        if gain_addr == 0x0048:
            addr1 = 0x00F9
        elif gain_addr == 0x004A:
            addr1 = 0x00FA
        elif gain_addr == 0x004C:
            addr1 = 0x00FB
        else:
            print("no valid register")
            return

        # measured_angle = self.get_meter_data1(addr1)
        total_angle = 0 # Initialize a variable to accumulate the sum of the results
        for i in range(10): # Run the loop 10 times, and use i as the loop variable
            measured_angle = self.get_meter_data1(addr1)
            time.sleep(0.5)
            total_angle += measured_angle  # Add the result to the total
        # Now, calculate the average using the number of iterations (i+1)
        average_angle = (total_angle / 10)  # i+1 because range starts at 0
        deg_2_rad = math.cos((average_angle* 3.141592654) / 180)
        print("deg_2_rad",deg_2_rad)

        error = ((deg_2_rad - 0.5) / 0.5) #0.5 = cos(60)
        print("error",error)

        new_angle_gain = error*g_phase
        print(f"new_angle_gain :{float(new_angle_gain)}")

        rounded_angle_gain = round(new_angle_gain)  # Round to the nearest integer
        print(f"round_new_angle_gain :",rounded_angle_gain)

        hex_rep = self.dec2hex_64bit(rounded_angle_gain)
        print(f"new_angle_gain (hex) : {hex_rep}", '\n')

        self.write_meter_data(gain_addr, hex_rep)

    def calibration(self):
        try:
            # Load the calibration data from mtr_cal.json
            with open('mtr_cal.json', 'r') as file:
                mtr_cal = json.load(file)
                calibration_data = mtr_cal.get("calibration_data", [])

            if not calibration_data:
                print("Warning: No calibration data found in mtr_cal.json")
                return

            # Iterate over the calibration data and call the write/read functions
            for data in calibration_data:
                try:
                    address = int(data["address"], 16)
                    value = int(data["value"], 16)
                    
                    # Write data and verify
                    self.write_meter_data(address, value)
                    read_value = self.get_meter_data1(address)
                    
                    # Optional: verify if written value matches read value
                    if read_value != value:
                        print(f"Warning: Write verification failed for address {hex(address)}")
                        print(f"Written: {hex(value)}, Read: {hex(read_value)}")
                    
                except (KeyError, ValueError) as e:
                    print(f"Error processing calibration data: {e}")
                    continue
        except FileNotFoundError:
            print("Error: mtr_cal.json file not found")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in mtr_cal.json")
        except Exception as e:
            print(f"Unexpected error during calibration: {e}")
    
    def checksum(self):
        checksum_3b = self.get_meter_data1(0x003B)
        self.write_meter_data(0x003B, checksum_3b)
        checksum_4d = self.get_meter_data1(0x004D)
        self.write_meter_data(0x004D, checksum_4d)
        checksum_57 = self.get_meter_data1(0x0057)
        self.write_meter_data(0x0057, checksum_57)
        checksum_6f = self.get_meter_data1(0x006F)
        self.write_meter_data(0x006F, checksum_6f)


# meter_control = MeterCalControl(port="COM10", baudrate=115200)

# # #Example usage:
# meter_control.get_meter_data1(0x0061)
 
    
