import logging
import serial
#import json

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PowerSupply:
    def __init__(self, port, baudrate=9600, timeout=1):
        """
        Initialize communication with the power supply.

        :param port: Serial port (e.g., 'COM3', '/dev/ttyUSB0')
        :param baudrate: Communication speed (default: 9600)
        :param timeout: Timeout for serial read operations
        """
        try:
            self.connection = serial.Serial(port, baudrate=baudrate, timeout=timeout)
            logging.info(f"Connected to power supply on {port} at {baudrate} baud.")
        except serial.SerialException as e:
            logging.error(f"Failed to open serial port: {e}")
            raise

    def send_frame(self, frame):
        """
        Send a binary frame to the power supply.

        :param frame: Frame as a bytearray
        """
        try:
            self.connection.write(frame)
            logging.debug(f"Frame sent: {frame.hex().upper()}")
        except serial.SerialTimeoutException:
            logging.error("Timeout while sending frame.")
        except Exception as e:
            logging.error(f"Error sending frame: {e}")
            raise

    def calculate_hex_values(self, value):
        """
        Calculate the hex representation of a value based on its scaling factor.
        
        :param value: The actual value (e.g., voltage or current).
        :return: Hexadecimal string of the scaled value.
        """
        # Ensure the value is within the acceptable range
        if value < 0:
            raise ValueError("Value cannot be negative.")

        # Choose the scaling factor
        if value < 10:
            scale = 10000  # Scale for very small values (1 digit)
        elif value < 1000:
            scale = 100   # Scale for values between 10 and 99 (2 digits)
        elif value < 100:
            scale = 10    # Scale for values between 100 and 999 (3 digits)
        else:
            raise ValueError("Value is too large for this scaling logic.")

        # Scale the value and return as a 4-digit hex
        scaled_value = int(value * scale)
        
        # Ensure the hex string is always 4 digits long, even if the value is small
        return f"{scaled_value:04X}"  # Format as 4-digit hex

    def get_power_factor_hex(self, power_factor):
        """
        Map the power factor to its corresponding hex value.

        :param power_factor: The power factor value (e.g., 1, 0.5L, 0.5C, etc.)
        :return: The hex string corresponding to the power factor.
        """
        power_factor_map = {
            1: "00 00",
            "0.5L": "17 70",  # 60
            "0.5C": "75 30",  # 30
            "0.8C": "7E 39",  # 32.3
            "0.8L": "0E 67"   # 36.8
        }
        
        return power_factor_map.get(power_factor, "00 00")  # Default to "00 00" if power factor is not found

    def set_voltage_and_current_Powerfactor(self, voltage, current, power_factor):
        """
        Send a frame to set voltage, current, and power factor on the power supply.

        :param voltage: Voltage in volts.
        :param current: Current in amps.
        :param power_factor: Power factor to be set.
        """
        voltage_hex = self.calculate_hex_values(voltage)
        current_hex = self.calculate_hex_values(current)
        
        # Get the power factor hex
        power_factor_hex = self.get_power_factor_hex(power_factor)

        # Construct the frame with power factor inserted
        frame = bytes.fromhex(
            f"F9 F9 F9 F9 F9 B1 10 00 02 00 10 20 13 88 {voltage_hex} {voltage_hex} {voltage_hex} 00 00 {current_hex} 00 00 {current_hex} 00 00 {current_hex} {power_factor_hex.replace(' ', '')} {power_factor_hex.replace(' ', '')} {power_factor_hex.replace(' ', '')} 2E E0 5D C0 00 00 05 66"
        )
        logging.info(f"Sending frame to set voltage: {voltage}V, current: {current}A, and power factor: {power_factor}")
        
        # Print the frame in hexadecimal format
        print(f"Frame to set voltage {voltage}V, current {current}A, and power factor {power_factor}: {frame.hex().upper()}")
        
        self.send_frame(frame)

    def reset_power_supply(self):
        """
        Send a predefined frame to reset the power supply.
        """
        frame = bytes.fromhex(
            "F9 F9 F9 F9 F9 B1 10 00 02 00 10 20 13 88 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 2E E0 5D C0 00 00 D4 04"
        )
        logging.info(f"Sending predefined frame to reset the power supply: {frame.hex().upper()}")
        self.send_frame(frame)

    def get_frame_response(self):
        """
        Send the frame "37 03 00 00 00 38 41 8E" to get a response from the power supply.

        :return: The response from the power supply or None if no response.
        """
        request_frame = bytes.fromhex("37 03 00 00 00 38 41 8E")
        self.send_frame(request_frame)

        # Wait for a response
        try:
            response = self.connection.read(1024)  # Read up to 128 bytes (adjust as needed)
            if response:
                logging.info(f"Received response: {response.hex().upper()}")
                return response
            else:
                logging.warning("No response received from power supply.")
                return None
        except serial.SerialTimeoutException:
            logging.error("Timeout while waiting for response.")
            return None
        except Exception as e:
            logging.error(f"Error receiving response: {e}")
            return None

    def close(self):
        """
        Close the connection to the power supply.
        """
        try:
            self.connection.close()
            logging.info("Connection to power supply closed.")
        except Exception as e:
            logging.error(f"Error closing connection: {e}")

    def extract_voltage_and_current(self, frame):
        """
        Extract the voltage, current, and power factor values from the received frame.

        :param frame: The received frame in bytes.
        :return: Extracted voltage, current, and power factor values.
        """
        # Extract the voltage (0A AB DF)
        voltage_bytes = frame[14:17]  # Assuming the voltage bytes are at positions 6 to 8
        voltage_scaled = int.from_bytes(voltage_bytes, byteorder='big')
        voltage = voltage_scaled / 10000  # Scale the value back by 10000
        
        voltage_bytes_Y = frame[18:21]  # Assuming the voltage bytes are at positions 6 to 8
        voltage_scaled = int.from_bytes(voltage_bytes_Y, byteorder='big')
        voltage_Y = voltage_scaled / 10000  # Scale the value back by 10000

        voltage_bytes_B = frame[22:25]  # Assuming the voltage bytes are at positions 6 to 8
        voltage_scaled = int.from_bytes(voltage_bytes_B, byteorder='big')
        voltage_B = voltage_scaled / 10000  # Scale the value back by 10000

        # Extract the current (73 5D 62)
        current_bytes = frame[26:29]  # Assuming the current bytes are at positions 18 to 20
        current_scaled = int.from_bytes(current_bytes, byteorder='big')
        current = current_scaled / 1000000  # Scale the value back by 1000000
        current /= 2  # Divide by 2 as per your original logic

        current_bytes_Y = frame[26:29]  # Assuming the current bytes are at positions 18 to 20
        current_scaled = int.from_bytes(current_bytes_Y, byteorder='big')
        current_Y = current_scaled / 1000000  # Scale the value back by 1000000
        current_Y /= 2  # Divide by 2 as per your original logic

        current_bytes_B = frame[26:29]  # Assuming the current bytes are at positions 18 to 20
        current_scaled = int.from_bytes(current_bytes_B, byteorder='big')
        current_B = current_scaled / 1000000  # Scale the value back by 1000000
        current_B /= 2  # Divide by 2 as per your original logic
        
        # Extract the power factor (bytes 106-109)
        power_factor_bytes = frame[114:117]  # Power factor bytes at positions 106 to 109
        power_factor_scaled = int.from_bytes(power_factor_bytes, byteorder='big')
        power_factor_value = power_factor_scaled / 10000.0  # Convert to decimal by dividing by 10000
        
        # Determine the power factor category based on the value
        if  power_factor_value <= 1.0:
            power_factor = "1.0 Unity"
        elif 59.0 <= power_factor_value <= 61.0:
            power_factor = "0.5L"
        elif 29.0 <= power_factor_value <= 31.0:
            power_factor = "0.5C"
        elif 31.0 <= power_factor_value <= 33.0:
            power_factor = "0.8C"
        elif 35.0 <= power_factor_value <= 37.0:
            power_factor = "0.8L"
        else:
            power_factor = "Unknown"  # If it falls out side of the known ranges
        
        # Log the extracted values and their corresponding hex
        voltage_hex = voltage_bytes.hex().upper()
        current_hex = current_bytes.hex().upper()
        power_factor_hex = power_factor_bytes.hex().upper()
        
        logging.info(f"Voltage (Hex): {voltage_hex}, Extracted Voltage R PHASE: {voltage}V")
        logging.info(f"Voltage (Hex): {voltage_hex}, Extracted Voltage Y PHASE: {voltage_Y}V")
        logging.info(f"Voltage (Hex): {voltage_hex}, Extracted Voltage B PHASE: {voltage_B}V")
        logging.info(f"Current (Hex): {current_hex}, Extracted Current R phase: {current}A")
        logging.info(f"Current (Hex): {current_hex}, Extracted Current Y phase: {current_Y}A")
        logging.info(f"Current (Hex): {current_hex}, Extracted Current B phase: {current_B}A")
        #logging.info(f"Power Factor (Hex): {power_factor_hex}, Extracted Power Factor: {power_factor_value} -> {power_factor}")
        
        return voltage, current
