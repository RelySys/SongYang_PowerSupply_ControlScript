import json
import logging
import serial
import sys
import os
import math
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
        meter_control = MeterCalControl(port="COM20", baudrate=115200) 

        # Example: Set voltage, current, and power factor from configuration for power supply
        set_power_supply = input("Do you want to change the power supply values? (yes/no): ").strip().lower()

        if set_power_supply == 'yes':
            power_supply.set_voltage_and_current_Powerfactor(
                voltage=settings["voltage"],
                current=settings["current"],
                power_factor=settings["power_factor"]
            )

        # Add a delay of 100ms before getting the response
            time.sleep(8)

        # Get frame response from the power supply
        # response = power_supply.get_frame_response()
        # if response:
        #     # Extract voltage and current from the response frame
        #     Voltage, Voltage_Y, Voltage_B, Current, Current_Y, Current_B = power_supply.extract_voltage_and_current(response)
        #     time.sleep(4)

        # print()

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

        print()

        # Ask the user if they want to calibrate voltage and current
        calibrate_vol_cur = input("Do you want to calibrate voltage and current? (yes/no): ").strip().lower()

        if calibrate_vol_cur == 'yes':
            print("writing default values")
            meter_control.calibration()
            time.sleep(2)
            print("\nCalibrating Voltage and Current...")
            def check_and_calibrate(phase, voltage, current):
                result = meter_control.get_meter_data(phase[0], phase[1])  # Read voltage
                print(f"Phase {phase[2]} result: {result}")
                if 219.5 <= result <= 220.5:
                    print(f"Calibration for Voltage Phase {phase[2]} successful.")
                elif 1.997 <= result <= 2.002:
                    print(f"Calibration for current Phase {phase[2]} successful.")
                else:
                    recalibrate = input("calibration is not accurate do you want to recalibarte it?  (yes/no):").strip().lower()
                    if recalibrate == 'yes':
                        print(f"Calibration for Phase {phase[2]} failed, recalibrating...")
                        meter_control.calibrate_vol_cur(phase[0], phase[1], phase[2], voltage)  # Recalibrate
                        time.sleep(1)  # Allow time for recalibration
                        check_and_calibrate(phase, voltage, current)  # Recursively check again
                    else:
                        print("voltage and current calibration done")

            # Voltage Calibration for R-Phase
            meter_control.calibrate_vol_cur(0x00D9, 0x00E9, 0x0061, settings["voltage"])  # Voltage calib Rphase
            # check_and_calibrate([0x00D9, 0x00E9, 0x0061], Voltage, Current)  # Check R-Phase

            # Voltage Calibration for Y-Phase
            meter_control.calibrate_vol_cur(0x00DA, 0x00EA, 0x0065, settings["voltage"])  # Voltage calib Yphase
            # check_and_calibrate([0x00DA, 0x00EA, 0x0065], Voltage_Y, Current_Y)  # Check Y-Phase

            # Voltage Calibration for B-Phase
            meter_control.calibrate_vol_cur(0x00DB, 0x00EB, 0x0069, settings["voltage"])  # Voltage calib Bphase
            # check_and_calibrate([0x00DB, 0x00EB, 0x0069], Voltage_B, Current_B)  # Check B-Phase

            # Current Calibration for R-Phase
            meter_control.calibrate_vol_cur(0x00DD, 0x00ED, 0x0062, settings["current"])  # Current calib Rphase
            # check_and_calibrate([0x00DD, 0x00ED, 0x0062], Voltage, Current)  # Check R-Phase current

            # Current Calibration for Y-Phase
            meter_control.calibrate_vol_cur(0x00DE, 0x00EE, 0x0066, settings["current"])  # Current calib Yphase
            # check_and_calibrate([0x00DE, 0x00EE, 0x0066], Voltage_Y, Current_Y)  # Check Y-Phase current

            # Current Calibration for B-Phase
            meter_control.calibrate_vol_cur(0x00DF, 0x00EF, 0x006A, settings["current"])  # Current calib Bphase
            # check_and_calibrate([0x00DF, 0x00EF, 0x006A], Voltage_B, Current_B)  # Check B-Phase current

            time.sleep(3)  # Wait for final calibration process to complete

            # meter_control.checksum()
        
            # If not calibrating voltage and current, ask if the user wants to calibrate phase angle
        calibrate_phase_angle = input("Do you want to calibrate the phase angle? (yes/no): ").strip().lower()

        if calibrate_phase_angle == 'yes':
            # Set power supply to specific values for phase angle calibration
            print("\nSetting Power Supply to Voltage: 220V, Current: 2A, Power Factor: 0.5 for Phase Angle Calibration...")
            power_supply.set_voltage_and_current_Powerfactor(
                voltage=220.0,  # Set to 220V
                current=2.0,    # Set to 2A
                power_factor="0.5L"  # Set power factor to 0.5
                )

            time.sleep(8)
                
            # Call the phase angle calibration function
            print("\nCalibrating Phase Angle...")
            meter_control.calibrate_phaseangle(0x0048)  # Voltage gain Rphase
            meter_control.calibrate_phaseangle(0x004A)  # Voltage gain Yphase
            meter_control.calibrate_phaseangle(0x004C)  # Voltage gain Bphase
            time.sleep(3)
            # meter_control.checksum()
            

        calibrate_Power = input("Do you want to calibrate the power? (yes/no): ").strip().lower()

        if calibrate_Power == 'yes':
            # Set power supply to specific values for phase angle calibration
            print("\nSetting Power Supply to Voltage: 220V, Current: 2A, Power Factor: 1 for Phase Angle Calibration...")
            power_supply.set_voltage_and_current_Powerfactor(
                voltage=220.0,  # Set to 220V
                current=2.0,    # Set to 2A
                power_factor=1  # Set power factor to 1
                )

            time.sleep(8)
                
            # Call the phase angle calibration function
            print("\nCalibrating Power...")
            meter_control.calibrate_power(0x0047)  # power r phase
            meter_control.calibrate_power(0x0049)  # power y phase
            meter_control.calibrate_power(0x004B)  # power b phase
            time.sleep(3)
            # meter_control.checksum()
            
            time.sleep(5)

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

        meter_control.get_meter_data1(0x00F8)   # Frq

        time.sleep(5)

    except serial.SerialException as e:
        logging.error(f"Serial communication error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
