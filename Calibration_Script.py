import logging
import serial
import struct
import json

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
    
    def calculate_scaling_factor(self, value, max_value):
        """
        Calculate the scaling factor dynamically based on the maximum value.

        :param value: The actual value (e.g., voltage, current).
        :param max_value: Maximum allowable value for the parameter.
        :return: Scaled integer value.
        """
        scaling_factor = 10 ** (len(str(max_value)) - 1)
        scaled_value = int(value * scaling_factor)
        if scaled_value > max_value:
            raise ValueError(f"Value {value} exceeds the maximum allowable limit of {max_value}.")
        return scaled_value

    def set_voltage_and_current(self, voltage, current, max_voltage=500.0, max_current=30.0):
        """
        Set voltage and current on the power supply using a binary frame.
        
        :param voltage: Voltage in volts.
        :param current: Current in amps.
        :param max_voltage: Maximum voltage supported by the power supply.
        :param max_current: Maximum current supported by the power supply.
        """
        # Preamble (Sync Bytes)
        preamble = b'\xf9\xf9\xf9\xf9\xf9'
        
        # Header: Frame identifier and length (calculated dynamically)
        frame_id = 0xB1
        
        # Calculate scaled voltage and current dynamically
        scaled_voltage = self.calculate_scaling_factor(voltage, max_voltage * 100)
        scaled_current = self.calculate_scaling_factor(current, max_current * 1000)
        
        # Payload construction
        command = 0x10  # Example command byte for setting voltage and current
        payload = struct.pack(
            '>BBHHHHHH',  # Big-endian format
            0x00, 0x02,  # Example fixed bytes
            command,
            scaled_voltage, scaled_voltage, scaled_voltage,  # Voltage for three phases
            scaled_current, scaled_current, scaled_current   # Current for three phases
        )
        
        # Length of the payload
        length = len(payload)
        
        # Checksum (last 2 bytes for error detection, using a sum mod 65536)
        checksum = sum(preamble + bytes([frame_id, length]) + payload) & 0xFFFF
        checksum_bytes = struct.pack('>H', checksum)
        
        # Construct full frame
        frame = preamble + bytes([frame_id, length]) + payload + checksum_bytes
        
        logging.info(f"Setting voltage: {voltage}V and current: {current}A")
        self.send_frame(frame)
    
    def close(self):
        """
        Close the connection to the power supply.
        """
        try:
            self.connection.close()
            logging.info("Connection to power supply closed.")
        except Exception as e:
            logging.error(f"Error closing connection: {e}")


if __name__ == "__main__":
    try:
        # Load configuration from file
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
        
        # Extract settings
        serial_config = config["serial"]
        settings = config["settings"]
        
        # Initialize PowerSupply object
        power_supply = PowerSupply(
            port=serial_config["port"],
            baudrate=serial_config.get("baudrate", 9600),
            timeout=serial_config.get("timeout", 1)
        )
        
        # Set voltage and current
        power_supply.set_voltage_and_current(
            voltage=settings["voltage"],
            current=settings["current"],
            max_voltage=settings.get("max_voltage", 500.0),
            max_current=settings.get("max_current", 30.0)
        )
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        power_supply.close()
