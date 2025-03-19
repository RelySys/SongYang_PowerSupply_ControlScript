import json
import logging
import serial
import sys
# import time  # Import time module for sleep function
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton
from Power_Supply_Control import PowerSupply  # Import PowerSupply class from Calibration_Script
# Add the path to the dlt645 module
sys.path.append(r'E:\Git\SongYang_PowerSupply_ControlScript\dlt645\dlt645')

import dlt645
from dlt645.constants import *
from Meter_Cal_Control import MeterCalControl  # Import the MeterControl class

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class CalibrationDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibration")
        # self.setGeometry(100, 100, 400, 200)
        self.resize(380, 250)

        # Label for the dialog question
        self.label = QtWidgets.QLabel(self)
        self.label.setText("Do you want to calibrate the meter?")
        self.label.setGeometry(80, 60, 250, 30)

        # Yes Button
        self.yes_button = QtWidgets.QPushButton("Yes", self)
        self.yes_button.setGeometry(50, 120, 100, 30)
        self.yes_button.clicked.connect(self.on_yes_clicked)

        # No Button
        self.no_button = QtWidgets.QPushButton("No", self)
        self.no_button.setGeometry(250, 120, 100, 30)
        self.no_button.clicked.connect(self.on_no_clicked)

        # Label for displaying "Calibrating............."
        self.calibration_status_label = QtWidgets.QLabel(self)
        self.calibration_status_label.setGeometry(100, 150, 200, 30)
        self.calibration_status_label.setText("")  # Initially empty

    def show_result_dialog(self):
        try:
            # Create and show the ResultDialog before closing current dialog
            result_dialog = ResultDialog(self.parent())
            self.close()  # Close the calibration dialog
            result_dialog.exec_()  # Show the result dialog modally
        except Exception as e:
            print(f"Error showing result dialog: {e}")

    def on_yes_clicked(self):
        # Update the label to show "Calibrating............."
        self.label.hide()
        self.yes_button.hide()
        self.no_button.hide()
        self.calibration_status_label.setText("Calibration started.............")

        print("writing default values")
        self.calibration_status_label.setText("Writing default values.............")
        meter_control.calibration()
        # Use QTimer to simulate delays without freezing the UI
        QtCore.QTimer.singleShot(5000, self.calibrate_vol_cur)  # Delay 2 seconds and call the start_calibration_process method

    def calibrate_vol_cur(self):
        # Start your calibration process after the delay
        print("\nCalibrating Voltage and Current...")
        self.calibration_status_label.setText("Calibrating Voltage and Current.............")

        # Simulate the calibration of each phase
        meter_control.calibrate_vol_cur(0x00D9, 0x00E9, 0x0061, settings["voltage"])  # Voltage calib Rphase
        meter_control.calibrate_vol_cur(0x00DA, 0x00EA, 0x0065, settings["voltage"])  # Voltage calib Yphase
        meter_control.calibrate_vol_cur(0x00DB, 0x00EB, 0x0069, settings["voltage"])  # Voltage calib Bphase
        meter_control.calibrate_vol_cur(0x00DD, 0x00ED, 0x0062, settings["current"])  # Current calib Rphase
        meter_control.calibrate_vol_cur(0x00DE, 0x00EE, 0x0066, settings["current"])  # Current calib Yphase
        meter_control.calibrate_vol_cur(0x00DF, 0x00EF, 0x006A, settings["current"])  # Current calib Bphase

        # Use QTimer to continue the process after a delay
        QtCore.QTimer.singleShot(3000, self.set_PA_Calibration)  # Delay 3 seconds and then call set_power_supply_1

    def set_PA_Calibration(self):
        self.calibration_status_label.setText("Calibrating Phase Angle.............")
        print("\nSetting Power Supply to Voltage: 220V, Current: 2A, Power Factor: 0.5 for Phase Angle Calibration...")
        power_supply.set_voltage_and_current_Powerfactor(
            voltage=220.0,  # Set to 220V
            current=3.0,    # Set to 2A
            power_factor="0.5L"  # Set power factor to 0.5
        )
        
        # Continue with phase angle calibration after the delay
        QtCore.QTimer.singleShot(8000, self.calibrate_phase_angle)  # Delay 8 seconds and call calibrate_phase_angle_1

    def calibrate_phase_angle(self):
        self.calibration_status_label.setText("Calibrating Phase Angle.............")
        print("\nCalibrating Phase Angle...")
        meter_control.calibrate_phaseangle(0x0048)  # Voltage gain Rphase
        meter_control.calibrate_phaseangle(0x004A)  # Voltage gain Yphase
        meter_control.calibrate_phaseangle(0x004C)  # Voltage gain Bphase

        # Proceed with the next step after another delay
        QtCore.QTimer.singleShot(3000, self.set_Power_Calibration)  # Delay 3 seconds and then call set_power_supply_2

    def set_Power_Calibration(self):
        self.calibration_status_label.setText("Calibrating Power.............")
        print("\nSetting Power Supply to Voltage: 220V, Current: 2A, Power Factor: 1 for Phase Angle Calibration...")
        power_supply.set_voltage_and_current_Powerfactor(
            voltage=220.0,  # Set to 220V
            current=3.0,    # Set to 2A
            power_factor=1  # Set power factor to 1
        )
        
        # Continue with the power calibration after the delay
        QtCore.QTimer.singleShot(8000, self.calibrate_power)  # Delay 8 seconds and then call calibrate_power

    def calibrate_power(self):
        self.calibration_status_label.setText("Calibrating Power.............")
        print("\nCalibrating Power...")
        meter_control.calibrate_power(0x0047)  # power r phase
        meter_control.calibrate_power(0x0049)  # power y phase
        meter_control.calibrate_power(0x004B)  # power b phase

        # Finally, finish calibration after a final delay
        QtCore.QTimer.singleShot(3000, self.finish_calibration)  # Delay 3 seconds and then call finish_calibration

    def finish_calibration(self):
        meter_control.checksum()
        print("\nCalibration Completed")
        QtCore.QTimer.singleShot(5000, lambda: self.calibration_status_label.setText("Calibration Completed!"))
        # Call the method after calibration completes
        # QtCore.QTimer.singleShot(100, self.show_calibration_results)
        QtCore.QTimer.singleShot(1000, self.show_result_dialog)

    def on_no_clicked(self):
        self.close()  # Close the dialog without doing anything

class ResultDialog2(QtWidgets.QDialog):
    def __init__(self, response_message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibration Results")
        self.setGeometry(500, 200, 400, 400)

        # Label to display the response message
        self.result_label = QtWidgets.QLabel(self)
        self.result_label.setText(response_message)
        self.result_label.setGeometry(20, 20, 360, 250)
        self.result_label.setWordWrap(True)  # Make text wrap

        # Button to close the result dialog
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setGeometry(300, 300, 55, 25)
        self.close_button.clicked.connect(self.close)  # Close the result dialog when clicked

class ResultDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ResultDialog, self).__init__(parent)
        self.setWindowTitle("Measurement Data")
        layout = QVBoxLayout()
        grid = QGridLayout()

        # Column Headers
        grid.addWidget(QLabel("Parameter"), 0, 0)
        grid.addWidget(QLabel("R-Phase (A)"), 0, 1)
        grid.addWidget(QLabel("Y-Phase (B)"), 0, 2)
        grid.addWidget(QLabel("B-Phase (C)"), 0, 3)

        # List of labels and corresponding functions to fetch values dynamically
        self.data = [
            ("Voltage Gain:", lambda: meter_control.get_meter_data1(0x0061),
                lambda: meter_control.get_meter_data1(0x0065), lambda: meter_control.get_meter_data1(0x0069)),
            ("Voltage (V):", lambda: meter_control.get_meter_data(0x00D9, 0x00E9),
                lambda: meter_control.get_meter_data(0x00DA, 0x00EA),
                lambda: meter_control.get_meter_data(0x00DB, 0x00EB)),
            ("Current Gain:", lambda: meter_control.get_meter_data1(0x0062),
                lambda: meter_control.get_meter_data1(0x0066), lambda: meter_control.get_meter_data1(0x006A)),
            ("Current (A):", lambda: meter_control.get_meter_data(0x00DD, 0x00ED),
                lambda: meter_control.get_meter_data(0x00DE, 0x00EE),
                lambda: meter_control.get_meter_data(0x00DF, 0x00EF)),
            ("Power (W):", lambda: meter_control.get_meter_data(0x00B1, 0x00C1),
                lambda: meter_control.get_meter_data(0x00B2, 0x00C2),
                lambda: meter_control.get_meter_data(0x00B3, 0x00C3))
        ]
        self.entries = []
        for i, (label, funcA, funcB, funcC) in enumerate(self.data, start=1):
            grid.addWidget(QLabel(label), i, 0)
            entryA = QLineEdit("000.000")
            entryB = QLineEdit("000.000")
            entryC = QLineEdit("000.000")
            entryA.setText(f"{funcA():.3f}")
            entryB.setText(f"{funcB():.3f}")
            entryC.setText(f"{funcC():.3f}")
            grid.addWidget(entryA, i, 1)
            grid.addWidget(entryB, i, 2)
            grid.addWidget(entryC, i, 3)
            self.entries.append((entryA, entryB, entryC, funcA, funcB, funcC))

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_values)
        grid.addWidget(self.refresh_button, len(self.data) + 1, 0, 1, 2)  # Add cancel button below "Calibrate"

        # Add "Calibrate" and "Cancel" buttons
        self.calibrate_button = QPushButton("Calibrate", self)
        self.calibrate_button.clicked.connect(self.close)  # Close the result dialog when clicked
        self.calibrate_button.clicked.connect(self.open_calibration_dialog)  # Open calibration dialog after closing result dialog
        grid.addWidget(self.calibrate_button, len(self.data) + 1, 4, 1, 2)  # Add button to grid layout (spanning first two columns)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.close)
        grid.addWidget(self.cancel_button, len(self.data) + 2, 4, 1, 2)  # Add cancel button below "Calibrate"

        layout.addLayout(grid)
        # layout.addWidget(self.refresh_button)
        self.setLayout(layout)

    def update_values(self):
        for entryA, entryB, entryC, funcA, funcB, funcC in self.entries:
            entryA.setText(f"{funcA():.3f}")
            entryB.setText(f"{funcB():.3f}")
            entryC.setText(f"{funcC():.3f}")

    def open_calibration_dialog(self):
        # Open the calibration dialog after closing the result dialog
        calibration_dialog = CalibrationDialog(self)
        calibration_dialog.exec_()

class Ui_Dialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # Try to load and set default values from config.json
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                # Set default values in input fields as placeholders
                self.ps_port_input.setPlaceholderText(f"Enter port (default: {config['serial']['port']})")
                self.ps_baudrate_input.setPlaceholderText(f"Enter baudrate (default: {config['serial']['baudrate']})")
                self.voltage_input.setPlaceholderText(f"Enter voltage (default: {config['settings']['voltage']})")
                self.current_input.setPlaceholderText(f"Enter current (default: {config['settings']['current']})")
                self.pf_input.setPlaceholderText(f"Enter power factor (default: {config['settings']['power_factor']})")
                self.meter_port_input.setPlaceholderText(f"Enter port (default: {config['mtr_serial']['port']})")
                self.meter_baudrate_input.setPlaceholderText(f"Enter baudrate (default: {config['mtr_serial']['baudrate']})")
        except Exception as e:
            print(f"Warning: Could not load default values from config.json: {str(e)}")

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1400, 800)
        
        # Set dialog background color to white
        Dialog.setStyleSheet("background-color: white;")

        # Add company logo at top-right
        self.logo_label = QtWidgets.QLabel(Dialog)
        self.logo_label.setGeometry(QtCore.QRect(1100, 20, 200, 80))  # Made logo slightly smaller
        self.logo_label.setObjectName("logo_label")
        self.logo_label.setScaledContents(True)
        
        try:
            # Load and set the company logo
            logo_path = r"E:\OneDrive - Invendis Technologies India Pvt. Ltd\D_Folder\MY_Documents\ALL_Projects\GIT_MFM\INV_logo.png"
            pixmap = QtGui.QPixmap(logo_path)
            if not pixmap.isNull():
                self.logo_label.setPixmap(pixmap)
                print("Successfully loaded logo from:", logo_path)
            else:
                raise FileNotFoundError("Could not load the image")
        except Exception as e:
            print(f"Error loading logo: {str(e)}")
            self.logo_label.setText("Invendis Technologies")
            self.logo_label.setStyleSheet("color: #333333; font-size: 16px; font-weight: bold; background-color: white;")

        # Create a grid layout for input fields
        self.grid_layout = QGridLayout()
        self.grid_layout.setVerticalSpacing(10)  # Reduced vertical spacing
        
        # Add section headers
        self.power_header = QLabel("Power Supply Configuration:", Dialog)
        self.power_header.setStyleSheet("font-size: 13px; font-weight: bold; padding-top: 5px;")
        self.grid_layout.addWidget(self.power_header, 0, 0, 1, 2)

        # Power Supply Serial Configuration
        self.ps_port_label = QLabel("Power Supply Port:", Dialog)
        self.ps_port_input = QLineEdit(Dialog)
        self.ps_port_input.setPlaceholderText("Enter port (e.g., COM1)")
        self.grid_layout.addWidget(self.ps_port_label, 1, 0)
        self.grid_layout.addWidget(self.ps_port_input, 1, 1)

        self.ps_baudrate_label = QLabel("Power Supply Baudrate:", Dialog)
        self.ps_baudrate_input = QLineEdit(Dialog)
        self.ps_baudrate_input.setPlaceholderText("Enter baudrate (e.g., 9600)")
        self.grid_layout.addWidget(self.ps_baudrate_label, 2, 0)
        self.grid_layout.addWidget(self.ps_baudrate_input, 2, 1)

        # Power Supply Values with reduced spacing
        self.voltage_label = QLabel("Voltage (V):", Dialog)
        self.voltage_input = QLineEdit(Dialog)
        self.voltage_input.setPlaceholderText("Enter voltage")
        self.grid_layout.addWidget(self.voltage_label, 3, 0)
        self.grid_layout.addWidget(self.voltage_input, 3, 1)
        
        self.current_label = QLabel("Current (A):", Dialog)
        self.current_input = QLineEdit(Dialog)
        self.current_input.setPlaceholderText("Enter current")
        self.grid_layout.addWidget(self.current_label, 4, 0)
        self.grid_layout.addWidget(self.current_input, 4, 1)
        
        self.pf_label = QLabel("Power Factor:", Dialog)
        self.pf_input = QLineEdit(Dialog)
        self.pf_input.setPlaceholderText("Enter power factor")
        self.grid_layout.addWidget(self.pf_label, 5, 0)
        self.grid_layout.addWidget(self.pf_input, 5, 1)

        # Meter Configuration Header
        self.meter_header = QLabel("Meter Configuration:", Dialog)
        self.meter_header.setStyleSheet("font-size: 13px; font-weight: bold; padding-top: 5px;")
        self.grid_layout.addWidget(self.meter_header, 6, 0, 1, 2)

        # Meter Serial Configuration
        self.meter_port_label = QLabel("Meter Port:", Dialog)
        self.meter_port_input = QLineEdit(Dialog)
        self.meter_port_input.setPlaceholderText("Enter port (e.g., COM2)")
        self.grid_layout.addWidget(self.meter_port_label, 7, 0)
        self.grid_layout.addWidget(self.meter_port_input, 7, 1)

        self.meter_baudrate_label = QLabel("Meter Baudrate:", Dialog)
        self.meter_baudrate_input = QLineEdit(Dialog)
        self.meter_baudrate_input.setPlaceholderText("Enter baudrate (e.g., 9600)")
        self.grid_layout.addWidget(self.meter_baudrate_label, 8, 0)
        self.grid_layout.addWidget(self.meter_baudrate_input, 8, 1)

        # Create a widget to hold the grid layout
        self.form_widget = QtWidgets.QWidget(Dialog)
        self.form_widget.setGeometry(QtCore.QRect(50, 50, 400, 350))  # Moved up and made more compact
        self.form_widget.setLayout(self.grid_layout)

        # Buttons moved up
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(60, 420, 100, 30))  # Moved up
        self.pushButton.setObjectName("pushButton")

        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(180, 420, 100, 30))  # Moved up
        self.pushButton_2.setObjectName("pushButton_2")

        # Style the input fields and labels
        input_style = """
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 11px;
                min-width: 180px;
                height: 20px;
            }
            QLabel {
                font-size: 11px;
                color: #333;
            }
            QPushButton {
                padding: 4px 12px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                min-width: 80px;
                height: 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        self.form_widget.setStyleSheet(input_style)

        self.retranslateUi(Dialog)

        # Connect the buttons to functions
        self.pushButton.clicked.connect(self.on_yes_clicked)
        self.pushButton_2.clicked.connect(self.on_no_clicked)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "MFM Calibration"))
        self.pushButton.setText(_translate("Dialog", "Apply"))
        # self.label_2.setText(_translate("Dialog", "Configure Power Supply and Meter Settings:"))
        self.pushButton_2.setText(_translate("Dialog", "Cancel"))

    def get_config_values(self):
        """Get the values from input fields or config.json if fields are empty"""
        try:
            # First try to load default values from config.json
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                default_values = {
                    "power_supply": {
                        "port": config["serial"]["port"],
                        "baudrate": config["serial"]["baudrate"],
                        "voltage": config["settings"]["voltage"],
                        "current": config["settings"]["current"],
                        "power_factor": config["settings"]["power_factor"]
                    },
                    "meter": {
                        "port": config["mtr_serial"]["port"],
                        "baudrate": config["mtr_serial"]["baudrate"]
                    }
                }
        except Exception as e:
            print(f"Warning: Could not load config.json: {str(e)}")
            default_values = None

        # Create a dictionary to store the final values
        config_values = {
            "power_supply": {},
            "meter": {}
        }

        # Power Supply Configuration
        ps_port = self.ps_port_input.text().strip()
        ps_baudrate = self.ps_baudrate_input.text().strip()
        voltage = self.voltage_input.text().strip()
        current = self.current_input.text().strip()
        pf = self.pf_input.text().strip()

        # Meter Configuration
        meter_port = self.meter_port_input.text().strip()
        meter_baudrate = self.meter_baudrate_input.text().strip()

        try:
            # For each value, use input if provided, otherwise use default from config.json
            if default_values:
                config_values["power_supply"]["port"] = ps_port if ps_port else default_values["power_supply"]["port"]
                config_values["power_supply"]["baudrate"] = int(ps_baudrate) if ps_baudrate else default_values["power_supply"]["baudrate"]
                config_values["power_supply"]["voltage"] = float(voltage) if voltage else default_values["power_supply"]["voltage"]
                config_values["power_supply"]["current"] = float(current) if current else default_values["power_supply"]["current"]
                config_values["power_supply"]["power_factor"] = float(pf) if pf else default_values["power_supply"]["power_factor"]
                config_values["meter"]["port"] = meter_port if meter_port else default_values["meter"]["port"]
                config_values["meter"]["baudrate"] = int(meter_baudrate) if meter_baudrate else default_values["meter"]["baudrate"]
            else:
                # If no config.json and fields are empty, show error
                if not all([ps_port, ps_baudrate, voltage, current, pf, meter_port, meter_baudrate]):
                    raise ValueError("Please enter all values or provide a valid config.json file")
                
                config_values["power_supply"]["port"] = ps_port
                config_values["power_supply"]["baudrate"] = int(ps_baudrate)
                config_values["power_supply"]["voltage"] = float(voltage)
                config_values["power_supply"]["current"] = float(current)
                config_values["power_supply"]["power_factor"] = float(pf)
                config_values["meter"]["port"] = meter_port
                config_values["meter"]["baudrate"] = int(meter_baudrate)

            return config_values

        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", 
                str(e) if "Please enter all values" in str(e) else 
                "Please enter valid values for all fields.\nBaudrate should be a number.\nVoltage, current, and power factor should be numeric values.")
            return None

    def on_yes_clicked(self):
        config_values = self.get_config_values()
        if config_values:
            try:
                # Initialize PowerSupply with new configuration
                try:
                    power_supply = PowerSupply(
                        port=config_values["power_supply"]["port"],
                        baudrate=config_values["power_supply"]["baudrate"],
                        timeout=1
                    )
                    print(f"Successfully connected to power supply on {config_values['power_supply']['port']}")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Power Supply Connection Error", 
                        f"Failed to connect to power supply: {str(e)}\nPlease check the port settings.")
                    return
                
                # Initialize MeterControl with new configuration
                try:
                    meter_control = MeterCalControl(
                        port=config_values["meter"]["port"],
                        baudrate=config_values["meter"]["baudrate"]
                    )
                    print(f"Successfully connected to meter on {config_values['meter']['port']}")
                except Exception as e:
                    # Close power supply if meter fails
                    if power_supply:
                        try:
                            power_supply.close()
                        except:
                            pass
                    QtWidgets.QMessageBox.critical(self, "Meter Connection Error", 
                        f"Failed to connect to meter: {str(e)}\nPlease check the port settings.")
                    return
                
                try:
                    # Set power supply values
                    power_supply.set_voltage_and_current_Powerfactor(
                        voltage=config_values["power_supply"]["voltage"],
                        current=config_values["power_supply"]["current"],
                        power_factor=config_values["power_supply"]["power_factor"]
                    )
                    print("Successfully set power supply parameters")
                    
                    # Start the calibration process
                    self.start_calibration()
                    
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Configuration Error", 
                        f"Failed to set power supply parameters: {str(e)}")
                    return
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", 
                    f"An unexpected error occurred: {str(e)}")
                return

    def on_no_clicked(self):
        # Close any existing connections before proceeding
        global power_supply, meter_control
        
        if power_supply:
            try:
                power_supply.close()
            except:
                pass
        if meter_control:
            try:
                meter_control.close()
            except:
                pass
                
        self.start_calibration()

    def start_calibration(self):
        try:
            result_dialog = ResultDialog(self.parent())
            self.close()  # Close the current dialog before showing the result dialog
            result_dialog.exec_()
            print("Calibration window opened successfully")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to open calibration window: {str(e)}")

    # def before_calib(self):
    #     # response_message = "Data Before Calibration\n\n"
    #     response_message = "R-Phase Voltage Gain: " + str(meter_control.get_meter_data1(0x0061)) + "\n"
    #     response_message += "R-Phase Voltage: " + str(meter_control.get_meter_data(0x00D9, 0x00E9)) + "\n"
    #     response_message += "Y-Phase Voltage Gain: " + str(meter_control.get_meter_data1(0x0065)) + "\n"
    #     response_message += "Y-Phase Voltage: " + str(meter_control.get_meter_data(0x00DA, 0x00EA)) + "\n"
    #     response_message += "B-Phase Voltage Gain: " + str(meter_control.get_meter_data1(0x0069)) + "\n"
    #     response_message += "B-Phase Voltage: " + str(meter_control.get_meter_data(0x00DB, 0x00EB)) + "\n"
        
    #     response_message += "R-Phase Current Gain: " + str(meter_control.get_meter_data1(0x0062)) + "\n"
    #     response_message += "R-Phase Current: " + str(meter_control.get_meter_data(0x00DD, 0x00ED)) + "\n"
    #     response_message += "Y-Phase Current Gain: " + str(meter_control.get_meter_data1(0x0066)) + "\n"
    #     response_message += "Y-Phase Current: " + str(meter_control.get_meter_data(0x00DE, 0x00EE)) + "\n"
    #     response_message += "B-Phase Current Gain: " + str(meter_control.get_meter_data1(0x006A)) + "\n"
    #     response_message += "B-Phase Current: " + str(meter_control.get_meter_data(0x00DF, 0x00EF)) + "\n"
        
    #     response_message += "R-Phase Power: " + str(meter_control.get_meter_data(0x00B1, 0x00C1)) + "\n"
    #     response_message += "Y-Phase Power: " + str(meter_control.get_meter_data(0x00B2, 0x00C2)) + "\n"
    #     response_message += "B-Phase Power: " + str(meter_control.get_meter_data(0x00B3, 0x00C3)) + "\n"

    #     return response_message


'''if __name__ == "__main__":
    power_supply = None  # Initialize variable to avoid NameError in the finally block
    meter_control = None  # Initialize MeterControl object
    # Load configuration from file
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    # Extract serial settings from config
    serial_config = config["serial"]
    settings = config["settings"]
    mtr_serial_config = config["mtr_serial"]

    # Initialize PowerSupply object
    power_supply = PowerSupply(
        port=serial_config["port"],
        baudrate=serial_config.get("baudrate", 9600),
        timeout=serial_config.get("timeout", 1)
    )

    # Initialize MeterControl object for the energy meter
    meter_control = MeterCalControl(
        port=mtr_serial_config["port"],
        baudrate=mtr_serial_config["baudrate"]
    ) 

    app = QtWidgets.QApplication(sys.argv)
    dialog = Ui_Dialog()  # Create dialog directly since Ui_Dialog is now a QDialog
    dialog.show()
    sys.exit(app.exec_())'''

if __name__ == "__main__":
    # Create QApplication first, before any other Qt widgets
    app = QtWidgets.QApplication(sys.argv)
    
    power_supply = None
    meter_control = None
    
    try:
        # Load configuration from file
        with open("config.json", "r") as config_file:
            config = json.load(config_file)

        serial_config = config["serial"]
        settings = config["settings"]
        mtr_serial_config = config["mtr_serial"]

        # Initialize PowerSupply with error handling
        try:
            power_supply = PowerSupply(
                port=serial_config["port"],
                baudrate=serial_config.get("baudrate", 9600),
                timeout=serial_config.get("timeout", 1)
            )
        except serial.SerialException as e:
            QtWidgets.QMessageBox.critical(None, "Error", 
                f"Failed to connect to power supply on {serial_config['port']}\nError: {str(e)}")
            sys.exit(1)

        # Initialize MeterControl with error handling
        try:
            meter_control = MeterCalControl(
                port=mtr_serial_config["port"],
                baudrate=mtr_serial_config["baudrate"]
            )
        except serial.SerialException as e:
            QtWidgets.QMessageBox.critical(None, "Error", 
                f"Failed to connect to meter on {mtr_serial_config['port']}\nError: {str(e)}")
            sys.exit(1)

        dialog = Ui_Dialog()
        dialog.show()
        sys.exit(app.exec_())

    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
        sys.exit(1)