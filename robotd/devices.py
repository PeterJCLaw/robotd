"""Actual device classes."""

import serial

from robotd import usb
from robotd.devices_base import Board, BoardMeta


class MotorBoard(Board):
    """Student Robotics-era Motor board."""

    lookup_keys = {
        'ID_MODEL': 'MCV3B',
        'ID_VENDOR': 'Student_Robotics',
        'subsystem': 'tty',
    }

    @classmethod
    def name(cls, node):
        """Board name - actually fetched over serial."""
        return node['ID_SERIAL_SHORT']

    def start(self):
        """Open connection to peripheral."""
        device = self.node['DEVNAME']
        self.connection = serial.Serial(device, baudrate=1000000)
        self.make_safe()

    def make_safe(self):
        """
        Set peripheral to a safe state.

        This is called after control connections have died.
        """
        # Brake both the motors
        self.connection.write(b'\x00\x02\x02\x03\x02')
        self._status = {'left': 'brake', 'right': 'brake'}

    def status(self):
        """Brief status description of the peripheral."""
        return self._status

    def _speed_byte(self, value):
        if value == 'free':
            return 1
        elif value == 'brake':
            return 2
        elif -1 <= value <= 1:
            return 128 + int(100 * value)
        else:
            raise ValueError("Non-understood speed")

    def command(self, cmd):
        """Run user-provided command."""
        self._status.update(cmd)
        self.connection.write(bytes([
            2, 2,
            3, 2,
            2, 1,
            3, 1,
            2, self._speed_byte(self._status['left']),
            3, self._speed_byte(self._status['right']),
        ]))


class BrainTemperatureSensor(Board):
    """
    Internal Raspberry Pi temperature sensor.

    This has extremely limited practical use and is basically here to serve as
    an example of how to add new devices.
    """

    lookup_keys = {
        'subsystem': 'thermal',
    }

    enabled = False

    @classmethod
    def name(cls, node):
        """Simple node name."""
        return node.sys_name

    def status(self):
        """Brief status description of the peripheral."""
        with open('{}/temp'.format(self.node.sys_path), 'r') as f:
            temp_milli_degrees = int(f.read())
        return {'temperature': temp_milli_degrees / 1000}


class PowerBoard(Board):
    lookup_keys = {
        'subsystem': 'usb',
        'ID_VENDOR': 'Student_Robotics',
        'ID_MODEL': 'Power_board_v4',
    }

    @classmethod
    def name(cls, node):
        """Board name."""
        return node['ID_SERIAL_SHORT']

    def start(self):
        """Open connection to peripheral."""
        path = tuple(int(x) for x in self.node['DEVNAME'].split('/')[4:])

        for device in usb.enumerate():
            if device.path == path:
                self.device = device
                break
        else:
            raise RuntimeError("Cannot open USB device by path")

        print("OPEN")
        self.device.open()
        print("SAFIFY")
        self.make_safe()
        print("DONE START")

    def _set_power_outputs(self, level):
        for command in (0, 1, 2, 3, 4, 5):
            self.device.control_write(
                64,
                level,
                command,
            )

    def make_safe(self):
        self._set_power_outputs(0)

    def status(self):
        return {}

    def command(self, cmd):
        if 'power' in cmd:
            power = bool(cmd['power'])
            self._set_power_outputs(1 if power else 0)

# Grab the full list of boards from the workings of the metaclass
BOARDS = BoardMeta.BOARDS
