import json
import logging
import serial
from Calibration_Script import PowerSupply  # Import PowerSupply class from Calibration_Script

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    power_supply = None  # Initialize variable to avoid NameError in the finally block

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

        # Example: Set voltage, current, and power factor from configuration
        power_supply.set_voltage_and_current_Powerfactor(
            voltage=settings["voltage"],
            current=settings["current"],
            power_factor=settings["power_factor"]
        )

        # Get frame response
        response = power_supply.get_frame_response()
        if response:
            logging.info(f"Frame response received: {response.hex().upper()}")
            # Extract voltage and current from the response frame
            voltage, current = power_supply.extract_voltage_and_current(response)

    except serial.SerialException as e:
        logging.error(f"Serial communication error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if power_supply is not None:
            power_supply.close()
