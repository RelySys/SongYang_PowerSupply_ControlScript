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
    def __init__(self, parent=None, meter_control=None):  # Add meter_control parameter
        super().__init__(parent)
        self.meter_control = meter_control  # Initialize meter_control attribute
        self.setWindowTitle("Calibration")
        self.resize(380, 250)

        # Create a container widget for the question and buttons
        question_container = QtWidgets.QWidget(self)
        question_container.setGeometry(QtCore.QRect(40, 60, 300, 150))
        question_layout = QVBoxLayout()

        # Add question label with centered styling
        self.question_label = QLabel("Do you want to calibrate the meter?", question_container)
        self.question_label.setStyleSheet("""
            font-size: 12px;
            color: #2c3e50;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            margin-bottom: 20px;
        """)
        self.question_label.setAlignment(QtCore.Qt.AlignCenter)
        question_layout.addWidget(self.question_label)

        # Create a horizontal layout for buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_style = """
            QPushButton {
                padding: 8px 25px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """

        # Yes Button
        self.yes_button = QtWidgets.QPushButton("Yes", question_container)
        self.yes_button.setStyleSheet(button_style)
        self.yes_button.clicked.connect(self.on_yes_clicked)
        
        # No Button
        self.no_button = QtWidgets.QPushButton("No", question_container)
        self.no_button.setStyleSheet(button_style)
        self.no_button.clicked.connect(self.on_no_clicked)

        # Add buttons to horizontal layout with spacing
        button_layout.addStretch()
        button_layout.addWidget(self.yes_button)
        button_layout.addSpacing(20)  # Space between buttons
        button_layout.addWidget(self.no_button)
        button_layout.addStretch()

        # Add button layout to main question layout
        question_layout.addLayout(button_layout)
        question_container.setLayout(question_layout)

        # Label for displaying calibration status
        self.calibration_status_label = QtWidgets.QLabel(self)
        self.calibration_status_label.setGeometry(QtCore.QRect(40, 180, 300, 30))
        self.calibration_status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.calibration_status_label.setStyleSheet("""
            font-size: 11px;
            color: #2c3e50;
            padding: 5px;
        """)
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
        self.question_label.hide()
        self.yes_button.hide()
        self.no_button.hide()
        self.calibration_status_label.setText("Calibration started.............")

        print("writing default values")
        self.calibration_status_label.setText("Writing default values.............")
        # meter_control.calibration()

        # Use QTimer to simulate delays without freezing the UI
        QtCore.QTimer.singleShot(5000, self.calibrate_vol_cur)  # Delay 2 seconds and call the start_calibration_process method

    def calibrate_vol_cur(self,meter_control=None,settings=None):
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

    def set_PA_Calibration(self,power_supply=None):
        self.calibration_status_label.setText("Calibrating Phase Angle.............")
        print("\nSetting Power Supply to Voltage: 220V, Current: 2A, Power Factor: 0.5 for Phase Angle Calibration...")
        power_supply.set_voltage_and_current_Powerfactor(
            voltage=220.0,  # Set to 220V
            current=3.0,    # Set to 2A
            power_factor="0.5L"  # Set power factor to 0.5
        )
        
        # Continue with phase angle calibration after the delay
        QtCore.QTimer.singleShot(8000, self.calibrate_phase_angle)  # Delay 8 seconds and call calibrate_phase_angle_1

    def calibrate_phase_angle(self,meter_control=None):
        self.calibration_status_label.setText("Calibrating Phase Angle.............")
        print("\nCalibrating Phase Angle...")
        meter_control.calibrate_phaseangle(0x0048)  # Voltage gain Rphase
        meter_control.calibrate_phaseangle(0x004A)  # Voltage gain Yphase
        meter_control.calibrate_phaseangle(0x004C)  # Voltage gain Bphase

        # Proceed with the next step after another delay
        QtCore.QTimer.singleShot(3000, self.set_Power_Calibration)  # Delay 3 seconds and then call set_power_supply_2

    def set_Power_Calibration(self,power_supply=None):
        self.calibration_status_label.setText("Calibrating Power.............")
        print("\nSetting Power Supply to Voltage: 220V, Current: 2A, Power Factor: 1 for Phase Angle Calibration...")
        power_supply.set_voltage_and_current_Powerfactor(
            voltage=220.0,  # Set to 220V
            current=3.0,    # Set to 2A
            power_factor=1  # Set power factor to 1
        )
        
        # Continue with the power calibration after the delay
        QtCore.QTimer.singleShot(8000, self.calibrate_power)  # Delay 8 seconds and then call calibrate_power

    def calibrate_power(self,meter_control=None):
        self.calibration_status_label.setText("Calibrating Power.............")
        print("\nCalibrating Power...")
        meter_control.calibrate_power(0x0047)  # power r phase
        meter_control.calibrate_power(0x0049)  # power y phase
        meter_control.calibrate_power(0x004B)  # power b phase

        # Finally, finish calibration after a final delay
        QtCore.QTimer.singleShot(3000, self.finish_calibration)  # Delay 3 seconds and then call finish_calibration

    def finish_calibration(self,meter_control=None):
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
    def __init__(self, parent=None, meter_control=None):
        super(ResultDialog, self).__init__(parent)
        self.meter_control = meter_control  # Store meter_control instance
        self.setWindowTitle("Measurement Data")
        layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(15)
        grid.setContentsMargins(15, 15, 15, 15)

        # Styles matching the main window
        label_style = """
            QLabel {
                font-size: 11px;
                color: #444;
                padding-right: 10px;
            }
        """
        
        input_style = """
            QLineEdit {
                padding: 6px;
                min-height: 25px;
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 150px;
            }
        """

        # Column Headers with styling
        header_style = """
            QLabel {
                font-size: 12px;
                color: #2c3e50;
                padding: 5px;
                font-weight: bold;
            }
        """
        
        param_header = QLabel("Parameter")
        param_header.setStyleSheet(header_style)
        r_phase_header = QLabel("R-Phase (A)")
        r_phase_header.setStyleSheet(header_style)
        y_phase_header = QLabel("Y-Phase (B)")
        y_phase_header.setStyleSheet(header_style)
        b_phase_header = QLabel("B-Phase (C)")
        b_phase_header.setStyleSheet(header_style)

        grid.addWidget(param_header, 0, 0)
        grid.addWidget(r_phase_header, 0, 1)
        grid.addWidget(y_phase_header, 0, 2)
        grid.addWidget(b_phase_header, 0, 3)

        # List of labels and corresponding functions to fetch values dynamically
        self.data = [
            ("Voltage Gain:", lambda: self.meter_control.get_meter_data1(0x0061),
             lambda: self.meter_control.get_meter_data1(0x0065), 
             lambda: self.meter_control.get_meter_data1(0x0069)),
            ("Voltage (V):", lambda: self.meter_control.get_meter_data(0x00D9, 0x00E9),
             lambda: self.meter_control.get_meter_data(0x00DA, 0x00EA),
             lambda: self.meter_control.get_meter_data(0x00DB, 0x00EB)),
            ("Current Gain:", lambda: self.meter_control.get_meter_data1(0x0062),
             lambda: self.meter_control.get_meter_data1(0x0066), 
             lambda: self.meter_control.get_meter_data1(0x006A)),
            ("Current (A):", lambda: self.meter_control.get_meter_data(0x00DD, 0x00ED),
             lambda: self.meter_control.get_meter_data(0x00DE, 0x00EE),
             lambda: self.meter_control.get_meter_data(0x00DF, 0x00EF)),
            ("Power (W):", lambda: self.meter_control.get_meter_data(0x00B1, 0x00C1),
             lambda: self.meter_control.get_meter_data(0x00B2, 0x00C2),
             lambda: self.meter_control.get_meter_data(0x00B3, 0x00C3))
        ]

        self.entries = []
        for i, (label, funcA, funcB, funcC) in enumerate(self.data, start=1):
            # Create and style label
            label_widget = QLabel(label)
            label_widget.setStyleSheet(label_style)
            grid.addWidget(label_widget, i, 0)

            # Create and style input fields
            entryA = QLineEdit()
            entryB = QLineEdit()
            entryC = QLineEdit()

            for entry in [entryA, entryB, entryC]:
                entry.setStyleSheet(input_style)
                entry.setReadOnly(True)

            entryA.setText(f"{funcA():.3f}")
            entryB.setText(f"{funcB():.3f}")
            entryC.setText(f"{funcC():.3f}")

            grid.addWidget(entryA, i, 1)
            grid.addWidget(entryB, i, 2)
            grid.addWidget(entryC, i, 3)
            self.entries.append((entryA, entryB, entryC, funcA, funcB, funcC))

        # Style buttons
        button_style = """
            QPushButton {
                padding: 8px 25px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """

        # Add buttons with consistent styling
        button_layout = QtWidgets.QHBoxLayout()
        
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.setStyleSheet(button_style)
        self.calibrate_button.clicked.connect(self.close)
        self.calibrate_button.clicked.connect(self.open_calibration_dialog)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(button_style)
        self.cancel_button.clicked.connect(self.close)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet(button_style)
        self.refresh_button.clicked.connect(self.update_values)

        # Add buttons to layout with proper spacing
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.calibrate_button)
        button_layout.addWidget(self.cancel_button)
        
        # Set up main layout
        layout.addLayout(grid)
        layout.addSpacing(20)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Set dialog size
        self.resize(700, 400)

    def update_values(self):
        for entryA, entryB, entryC, funcA, funcB, funcC in self.entries:
            entryA.setText(f"{funcA():.3f}")
            entryB.setText(f"{funcB():.3f}")
            entryC.setText(f"{funcC():.3f}")

def open_calibration_dialog(self):
    # Open the calibration dialog after closing the result dialog
    calibration_dialog = CalibrationDialog(self, meter_control=self.meter_control)  # Pass meter_control
    calibration_dialog.exec_()

class Ui_Dialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.power_supply = None  # Add this line
        self.meter_control = None  # Add this line
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
        Dialog.resize(1300, 600)
        # Add company logo at top-right
        self.logo_label = QtWidgets.QLabel(Dialog)
        self.logo_label.setGeometry(QtCore.QRect(1050, 10, 200, 100))  # Made logo slightly smaller
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
            self.logo_label.setStyleSheet(
                "color: #333333; font-size: 16px; font-weight: bold; background-color: white;")

        # Create a grid layout for input fields with better spacing
        self.grid_layout = QGridLayout()
        self.grid_layout.setVerticalSpacing(12)  # Increased spacing between rows
        self.grid_layout.setHorizontalSpacing(15)  # Added horizontal spacing
        self.grid_layout.setContentsMargins(15, 15, 15, 15)  # Larger margins

        # Add section headers with refined styling
        self.power_header = QLabel("Power Supply Configuration", Dialog)
        self.power_header.setStyleSheet("""
            font-size: 12px; 
            min-height: 20px;
            color: #2c3e50;
            padding: 10px 0px;
            margin-bottom: 12px;
        """)
        self.grid_layout.addWidget(self.power_header, 0, 0, 1, 2)

        # Common styles
        input_style = """
            QLineEdit {
                padding: 6px;
                min-height: 25px;
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 200px;
            }
        """
        label_style = """
            QLabel {
                font-size: 11px;
                color: #444;
                padding-right: 10px;
            }
        """

        # Power Supply Serial Configuration with better spacing
        self.ps_port_label = QLabel("Port:", Dialog)
        self.ps_port_label.setStyleSheet(label_style)
        self.ps_port_input = QLineEdit(Dialog)
        self.ps_port_input.setPlaceholderText("Enter port (e.g., COM1)")
        self.ps_port_input.setStyleSheet(input_style)
        self.grid_layout.addWidget(self.ps_port_label, 1, 0)
        self.grid_layout.addWidget(self.ps_port_input, 1, 1)

        self.ps_baudrate_label = QLabel("Baudrate:", Dialog)
        self.ps_baudrate_label.setStyleSheet(label_style)
        self.ps_baudrate_input = QLineEdit(Dialog)
        self.ps_baudrate_input.setPlaceholderText("Enter baudrate (e.g., 9600)")
        self.ps_baudrate_input.setStyleSheet(input_style)
        self.grid_layout.addWidget(self.ps_baudrate_label, 2, 0)
        self.grid_layout.addWidget(self.ps_baudrate_input, 2, 1)

        # Add a small spacer
        spacer_label = QLabel("", Dialog)
        spacer_label.setStyleSheet("min-height: 10px;")
        self.grid_layout.addWidget(spacer_label, 3, 0)

        # Power Supply Values
        self.voltage_label = QLabel("Voltage:", Dialog)
        self.voltage_label.setStyleSheet(label_style)
        self.voltage_input = QLineEdit(Dialog)
        self.voltage_input.setPlaceholderText("Enter voltage (V)")
        self.voltage_input.setStyleSheet(input_style)
        self.grid_layout.addWidget(self.voltage_label, 4, 0)
        self.grid_layout.addWidget(self.voltage_input, 4, 1)

        self.current_label = QLabel("Current:", Dialog)
        self.current_label.setStyleSheet(label_style)
        self.current_input = QLineEdit(Dialog)
        self.current_input.setPlaceholderText("Enter current (A)")
        self.current_input.setStyleSheet(input_style)
        self.grid_layout.addWidget(self.current_label, 5, 0)
        self.grid_layout.addWidget(self.current_input, 5, 1)

        self.pf_label = QLabel("Power Factor:", Dialog)
        self.pf_label.setStyleSheet(label_style)
        self.pf_input = QLineEdit(Dialog)
        self.pf_input.setPlaceholderText("Enter power factor")
        self.pf_input.setStyleSheet(input_style)
        self.grid_layout.addWidget(self.pf_label, 6, 0)
        self.grid_layout.addWidget(self.pf_input, 6, 1)

        # Add another spacer before Meter Configuration
        spacer_label2 = QLabel("", Dialog)
        spacer_label2.setStyleSheet("min-height: 15px;")
        self.grid_layout.addWidget(spacer_label2, 7, 0)

        # Meter Configuration Header
        self.meter_header = QLabel("Meter Configuration", Dialog)
        self.meter_header.setStyleSheet("""
            font-size: 12px;
            min-height: 20px; 
            color: #2c3e50;
            padding: 10px 0px;
            margin-bottom: 10px;
        """)
        self.grid_layout.addWidget(self.meter_header, 8, 0, 1, 2)

        # Meter Serial Configuration
        self.meter_port_label = QLabel("Port:", Dialog)
        self.meter_port_label.setStyleSheet(label_style)
        self.meter_port_input = QLineEdit(Dialog)
        self.meter_port_input.setPlaceholderText("Enter port (e.g., COM2)")
        self.meter_port_input.setStyleSheet(input_style)
        self.grid_layout.addWidget(self.meter_port_label, 9, 0)
        self.grid_layout.addWidget(self.meter_port_input, 9, 1)

        self.meter_baudrate_label = QLabel("Baudrate:", Dialog)
        self.meter_baudrate_label.setStyleSheet(label_style)
        self.meter_baudrate_input = QLineEdit(Dialog)
        self.meter_baudrate_input.setPlaceholderText("Enter baudrate (e.g., 9600)")
        self.meter_baudrate_input.setStyleSheet(input_style)
        self.grid_layout.addWidget(self.meter_baudrate_label, 10, 0)
        self.grid_layout.addWidget(self.meter_baudrate_input, 10, 1)

        # Create a widget to hold the grid layout
        self.form_widget = QtWidgets.QWidget(Dialog)
        self.form_widget.setGeometry(QtCore.QRect(50, 30, 400, 380))
        self.form_widget.setLayout(self.grid_layout)

        # Center the calibration question section
        question_container = QtWidgets.QWidget(Dialog)
        question_container.setGeometry(QtCore.QRect(450, 150, 400, 150))  # Moved to center-right
        question_layout = QVBoxLayout()

        # Add question label with centered styling
        self.question_label = QLabel("Do you want to set the power supply?", question_container)
        self.question_label.setStyleSheet("""
            font-size: 12px;
            color: #2c3e50;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            margin-bottom: 20px;
        """)
        self.question_label.setAlignment(QtCore.Qt.AlignCenter)
        question_layout.addWidget(self.question_label)

        # Create a horizontal layout for buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_style = """
            QPushButton {
                padding: 8px 25px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """

        self.yes_button = QtWidgets.QPushButton("Yes", question_container)
        self.yes_button.setStyleSheet(button_style)
        self.yes_button.clicked.connect(self.on_yes_clicked)
        
        self.no_button = QtWidgets.QPushButton("No", question_container)
        self.no_button.setStyleSheet(button_style)
        self.no_button.clicked.connect(self.on_no_clicked)

        # Add buttons to horizontal layout with spacing
        button_layout.addStretch()
        button_layout.addWidget(self.yes_button)
        button_layout.addSpacing(20)  # Space between buttons
        button_layout.addWidget(self.no_button)
        button_layout.addStretch()

        # Add button layout to main question layout
        question_layout.addLayout(button_layout)
        question_container.setLayout(question_layout)

        self.retranslateUi(Dialog)

        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "MFM Calibration"))
        self.yes_button.setText(_translate("Dialog", "Yes"))
        self.no_button.setText(_translate("Dialog", "No"))

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

    def start_calibration(self):
        try:
            # Pass meter_control to ResultDialog
            result_dialog = ResultDialog(parent=self.parent(), meter_control=self.meter_control)
            result_dialog.exec_()
            print("calibration finished")
            self.open_calibration_dialog()  # Call open_calibration_dialog on the Ui_Dialog object
        except Exception as e:
            print(f"Error in start_calibration: {e}")

    def on_yes_clicked(self):
        config_values = self.get_config_values()
        if config_values:
            try:
                # Close existing connections if they exist
                if self.power_supply is not None:
                    try:
                        self.power_supply.ser.close()
                    except:
                        pass
                if self.meter_control is not None:
                    try:
                        self.meter_control.ser.close()
                    except:
                        pass

                # Initialize PowerSupply with new configuration
                try:
                    self.power_supply = PowerSupply(
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
                    self.meter_control = MeterCalControl(
                        port=config_values["meter"]["port"],
                        baudrate=config_values["meter"]["baudrate"]
                    )
                    print(f"Successfully connected to meter on {config_values['meter']['port']}")
                except Exception as e:
                    # Close power supply if meter fails
                    if self.power_supply:
                        try:
                            self.power_supply.ser.close()
                        except:
                            pass
                    QtWidgets.QMessageBox.critical(self, "Meter Connection Error", 
                        f"Failed to connect to meter: {str(e)}\nPlease check the port settings.")
                    return
                
                try:
                    # Set power supply values
                    self.power_supply.set_voltage_and_current_Powerfactor(
                        voltage=config_values["power_supply"]["voltage"],
                        current=config_values["power_supply"]["current"],
                        power_factor=config_values["power_supply"]["power_factor"]
                    )
                    print("Successfully set power supply parameters")
                    # Set a delay of 8 seconds using QTimer, then execute the calibration process
                    QtCore.QTimer.singleShot(8000, lambda: self.start_calibration())
                    
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Configuration Error", 
                        f"Failed to set power supply parameters: {str(e)}")
                    return
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", 
                    f"An unexpected error occurred: {str(e)}")
                return

    def on_no_clicked(self):
        try:
            # Load default values from config.json
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                
            # Close existing connections if they exist
            if self.power_supply is not None:
                try:
                    self.power_supply.ser.close()
                except:
                    pass
            if self.meter_control is not None:
                try:
                    self.meter_control.ser.close()
                except:
                    pass

            # Initialize with default values
            try:
                self.power_supply = PowerSupply(
                    port=config["serial"]["port"],
                    baudrate=config["serial"]["baudrate"],
                    timeout=1
                )
                print(f"Successfully connected to power supply using default settings")
                
                self.meter_control = MeterCalControl(
                    port=config["mtr_serial"]["port"],
                    baudrate=config["mtr_serial"]["baudrate"]
                )
                print(f"Successfully connected to meter using default settings")

                # Set power supply values using default settings
                self.power_supply.set_voltage_and_current_Powerfactor(
                    voltage=config["settings"]["voltage"],
                    current=config["settings"]["current"],
                    power_factor=config["settings"]["power_factor"]
                )
                print("Successfully set default power supply parameters")
                
                # Start calibration after delay
                QtCore.QTimer.singleShot(8000, self.start_calibration)

            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Connection Error", 
                    f"Failed to initialize with default values: {str(e)}")
                return

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to load config.json: {str(e)}")
            return


if __name__ == "__main__":
    # Create QApplication first, before any other Qt widgets
    app = QtWidgets.QApplication(sys.argv)
    
    try:
        # Load configuration from file
        with open("config.json", "r") as config_file:
            config = json.load(config_file)

        dialog = Ui_Dialog()
        dialog.show()
        sys.exit(app.exec_())

    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
        sys.exit(1)