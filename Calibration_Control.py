import json
import logging
import serial
import sys
import os
import time  # Import time module for sleep function
from Power_Supply_Control import PowerSupply  # Import PowerSupply class from Calibration_Script
# Add the path to the dlt645 module
sys.path.append(r'E:\Git\SongYang_PowerSupply_ControlScript\dlt645\dlt645')

import dlt645
from dlt645.constants import *
from Meter_Cal_Control import MeterCalControl  # Import the MeterControl class

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    power_supply = None  # Initialize variable to avoid NameError in the finally block
    meter_control = None  # Initialize MeterControl object

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

        # Initialize MeterControl object for the energy meter
        meter_control = MeterCalControl(port="COM19", baudrate=115200) 

       

        # Example: Set voltage, current, and power factor from configuration for power supply
        power_supply.set_voltage_and_current_Powerfactor(
            voltage=settings["voltage"],
            current=settings["current"],
            power_factor=settings["power_factor"]
        )

        # Add a delay of 100ms before getting the response
        time.sleep(3)

        # Get frame response from the power supply
        response = power_supply.get_frame_response()
        if response:
           #logging.info(f"Frame response received: {response.hex().upper()}")
            # Extract voltage and current from the response frame
            voltage, current = power_supply.extract_voltage_and_current(response)
        print()

       # to disturb calibration 
        print("\nDisturbing Voltage and Current registers\n")

        meter_control.write_meter_data(0x0061, 0x8000)  # Rphase Voltage gain reg
        meter_control.write_meter_data(0x0065, 0x8000)  # Yphase Voltage gain reg
        meter_control.write_meter_data(0x0069, 0x8000)  # Bphase Voltage gain reg

        meter_control.write_meter_data(0x0062, 0x8000)  # Rphase Current gain reg
        meter_control.write_meter_data(0x0066, 0x8000)  # Yphase Current gain reg
        meter_control.write_meter_data(0x006A, 0x8000)  # Bphase Current gain reg

        print("\n reading Voltage, Current and Power registers after disturbance\n")

        meter_control.get_meter_data(0x00D9, 0x00E9)  # R-Phase //read voltage
        meter_control.get_meter_data(0x00DA, 0x00EA)  # Y-Phase //read voltage
        meter_control.get_meter_data(0x00DB, 0x00EB)  # B-Phase //read voltage

        meter_control.get_meter_data(0x00DD, 0x00ED)  # R-Phase //read current
        meter_control.get_meter_data(0x00DE, 0x00EE)  # R-Phase //read current
        meter_control.get_meter_data(0x00DF, 0x00EF)  # R-Phase //read current

        meter_control.get_meter_data(0x00B1, 0x00C1)  # R-Phase //read power
        meter_control.get_meter_data(0x00B2, 0x00C2)  # y-Phase //read power
        meter_control.get_meter_data(0x00B3, 0x00C3)  # B-Phase //read power

        # disturb gain registers
        # print("\nDisturbing phase angle gain registers\n")

        # meter_control.write_meter_data(0x0061, 0x8000)  # Rphase Phase voltage gain reg
        # meter_control.write_meter_data(0x0065, 0x8000)  # Yphase Phase angle voltage gain reg
        # meter_control.write_meter_data(0x0069, 0x8000)  # Bphase Phase angle voltage gain reg

        # meter_control.write_meter_data(0x0062, 0x8000)  # Rphase Phase angle current gain reg
        # meter_control.write_meter_data(0x0066, 0x8000)  # Yphase Phase angle current gain reg
        # meter_control.write_meter_data(0x006A, 0x8000)  # Bphase Phase angle current gain reg

        # print("\n reading Phase gain registers after disturbance\n")

        # meter_control.get_meter_data1(0x0061)  # R-Phase //read voltage
        # meter_control.get_meter_data1(0x0065)  # Y-Phase //read voltage
        # meter_control.get_meter_data1(0x0069)  # B-Phase //read voltage

        # meter_control.get_meter_data1(0x0062)  # R-Phase //read current
        # meter_control.get_meter_data1(0x0066)  # R-Phase //read current
        # meter_control.get_meter_data1(0x006A)  # R-Phase //read current

        print("\nBEFORE CALIBRATION DATA:\n")

        meter_control.get_meter_data1(0x0061)   # Voltage gain Rphase
        meter_control.get_meter_data(0x00D9, 0x00E9)  # R-Phase //read voltage
        meter_control.get_meter_data1(0x0065)   # Voltage gain Yphase
        meter_control.get_meter_data(0x00DA, 0x00EA)  # Y-Phase //read voltage
        meter_control.get_meter_data1(0x0069)   # Voltage gain Bphase
        meter_control.get_meter_data(0x00DB, 0x00EB)  # B-Phase //read voltage

        meter_control.get_meter_data1(0x0062)   # Current gain Rphase
        meter_control.get_meter_data(0x00DD, 0x00ED)  # R-Phase //read current
        meter_control.get_meter_data1(0x0066)   # Current gain Yphase
        meter_control.get_meter_data(0x00DE, 0x00EE)  # R-Phase //read current
        meter_control.get_meter_data1(0x006A)   # Current gain Bphase
        meter_control.get_meter_data(0x00DF, 0x00EF)  # R-Phase //read current

        meter_control.get_meter_data(0x00B1, 0x00C1)  # R-Phase //read power
        meter_control.get_meter_data(0x00B2, 0x00C2)  # y-Phase //read power
        meter_control.get_meter_data(0x00B3, 0x00C3)  # B-Phase //read power


        print("\nCalibrating Voltage and current.......\n")

        meter_control.calibrate_vol_cur(0x00D9, 0x00E9, 0x0061,  settings["voltage"])   #Voltage calib Rph
        meter_control.calibrate_vol_cur(0x00DA, 0x00EA, 0x0065, settings["voltage"])  #ltage calib Yphase
        meter_control.calibrate_vol_cur(0x00DB, 0x00EB, 0x0069, settings["voltage"]) # Voltage calib B phase

        meter_control.calibrate_vol_cur(0x00DD, 0x00ED, 0x0062, settings["current"])     # Current calib
        meter_control.calibrate_vol_cur(0x00DE, 0x00EE, 0x0066, settings["current"])  # Current calib
        meter_control.calibrate_vol_cur(0x00DF, 0x00EF, 0x006A,settings["current"])     # Current calib

        # print("\nCalibrating Phase angle.......\n")

        # meter_control.calibrate_phaseangle(0x0048)  # Voltage gain Rphase
        # meter_control.calibrate_phaseangle(0x004A)  # Voltage gain Yphase
        # meter_control.calibrate_phaseangle(0x004C)  # Voltage gain Yphase

        # print("\nCalibrating Power.......\n")

        # meter_control.calibrate_power(0x0047)  # power Rphase
        # meter_control.calibrate_power(0x0049)  # power Yphase
        # meter_control.calibrate_power(0x004B)  # power Yphase

        time.sleep(3)

        print("\nAFTER CALIBRATION DATA:\n")

        meter_control.get_meter_data1(0x0061)   # Voltage gain Rphase
        meter_control.get_meter_data(0x00D9, 0x00E9)  # R-Phase //read voltage
        meter_control.get_meter_data1(0x0065)   # Voltage gain Yphase
        meter_control.get_meter_data(0x00DA, 0x00EA)  # Y-Phase //read voltage
        meter_control.get_meter_data1(0x0069)   # Voltage gain Bphase
        meter_control.get_meter_data(0x00DB, 0x00EB)  # B-Phase //read voltage

        meter_control.get_meter_data1(0x0062)   # Current gain Rphase
        meter_control.get_meter_data(0x00DD, 0x00ED)  # R-Phase //read current
        meter_control.get_meter_data1(0x0066)   # Current gain Yphase
        meter_control.get_meter_data(0x00DE, 0x00EE)  # Y-Phase //read current
        meter_control.get_meter_data1(0x006A)   # Current gain Bphase
        meter_control.get_meter_data(0x00DF, 0x00EF)  # B-Phase //read current

        meter_control.get_meter_data(0x00B1, 0x00C1)  # R-Phase //read power
        meter_control.get_meter_data(0x00B2, 0x00C2)  # y-Phase //read power
        meter_control.get_meter_data(0x00B3, 0x00C3)  # B-Phase //read power

        meter_control.get_meter_data1(0x00F9)   # PA Rphase
        meter_control.get_meter_data1(0x00FA)   # PA Yphase
        meter_control.get_meter_data1(0x00FB)   # PA Bphase

        meter_control.get_meter_data1(0x00F8)   #Frq


    except serial.SerialException as e:
        logging.error(f"Serial communication error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    #finally:
        #if power_supply is not None:
           # power_supply.close()
