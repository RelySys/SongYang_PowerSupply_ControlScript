import logging
import serial
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

    def calculate_hex_values(self, value):
        """
        Calculate the hex representation of a value based on its scaling factor.

        :param value: The actual value (e.g., voltage or current).
        :return: Hexadecimal string of the scaled value.
        """
        # Determine the scaling factor based on the number of digits before the decimal point
        value_str = str(value).split(".")[0]  # Get the integer part of the number as a string
        num_digits = len(value_str)

        if num_digits == 1:
            scale = 10000
        elif num_digits == 2:
            scale = 1000
        elif num_digits == 3:
            scale = 100
        else:
            raise ValueError("Value is too large for this scaling logic.")

        # Scale the value and return as a 4-digit hex
        scaled_value = int(value * scale)
        return f"{scaled_value:04X}"  # Format as 4-digit hex

    def set_voltage_and_current(self, voltage, current):
        """
        Send a frame to set voltage and current on the power supply.

        :param voltage: Voltage in volts.
        :param current: Current in amps.
        """
        voltage_hex = self.calculate_hex_values(voltage)
        current_hex = self.calculate_hex_values(current)

        frame = bytes.fromhex(
            f"F9 F9 F9 F9 F9 B1 10 00 02 00 10 20 13 88 {voltage_hex} {voltage_hex} {voltage_hex} 00 00 {current_hex} 00 00 {current_hex} 00 00 {current_hex} 00 00 00 00 00 00 2E E0 5D C0 00 00 2F A5"
        )
        logging.info(f"Sending frame to set voltage: {voltage}V and current: {current}A")
        
        # Print the frame in hexadecimal format
        print(f"Frame to set voltage {voltage}V and current {current}A: {frame.hex().upper()}")
        
        self.send_frame(frame)

    def reset_power_supply(self):
        """
        Send a predefined frame to reset the power supply.
        """
        frame = bytes.fromhex(
            "F9 F9 F9 F9 F9 B1 10 00 02 00 10 20 13 88 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 2E E0 5D C0 00 00 7C B2"
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
            response = self.connection.read(128)  # Read up to 128 bytes (adjust as needed)
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


if __name__ == "__main__":
    power_supply = None  # Initialize variable to avoid NameError in the `finally` block

    try:
        # Load configuration from file
        with open("config.json", "r") as config_file:
            config = json.load(config_file)

        # Extract serial settings from config
        serial_config = config["serial"]
        settings = config["settings"]

        # Initialize PowerSupply object
        power_supply = PowerSupply(
            port=serial_config["port"],
            baudrate=serial_config.get("baudrate", 9600),
            timeout=serial_config.get("timeout", 1)
        )

        # Example: Set voltage and current from configuration
        power_supply.set_voltage_and_current(
            voltage=settings["voltage"],
            current=settings["current"]
        )

        # Example: Reset the power supply
        #power_supply.reset_power_supply()

        # Get frame response
        response = power_supply.get_frame_response()
        if response:
            logging.info(f"Frame response received: {response.hex().upper()}")

    except serial.SerialException as e:
        logging.error(f"Serial communication error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if power_supply is not None:
            power_supply.close()
