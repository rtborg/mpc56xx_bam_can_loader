import sys
import errno
import argparse

import can

# CAN bus variables
ID_SEND_PASSWORD = 0x011  # Password sent with CAN ID 0x011
ID_SEND_PASSWORD_ECHO = 0x001  # Password echoed with CAN ID 0x001
ID_SEND_ADDRESS = 0x012  # VLE and address/size sent with CAN ID 0x012
ID_SEND_ADDRESS_ECHO = 0x002  # VLE and address/size echoed with CAN ID 0x002
ID_SEND_DATA = 0x013  # Rest of data sent wit CAN ID 0x013
ID_SEND_DATA_ECHO = 0x003  # Rest of data echo CAN ID
LOADING_ADDRESS = bytearray(
    [0x40, 0x00, 0x01, 0x00]
)  # Loading address is always the same

# Default MPC5646 password
DEFAULT_PASSWORD = 0xFEEDFACECAFEBEEF

# Copied from https://github.com/hardbyte/python-can/blob/develop/can/logger.py
def _create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""

    parser.add_argument(
        "interface",
        help="""Specify the backend CAN interface to use.""",
    )

    parser.add_argument("channel", help="""CAN channel (can0 for example)""")

    parser.add_argument("bitrate", type=int, help="Bitrate to use for the CAN bus.")

    parser.add_argument(
        "ram_image",
        type=str,
        help="path to RAM image to be loaded to target (.bin format)",
    )

    parser.add_argument(
        "--password",
        type=int,
        help="Target password as 8-byte hex number. Leave blank for using default password.",
    )


class CANLoader:
    """MPC56xx CAN bus Boot Assist Module loader"""

    def __init__(self, interface, channel, bitrate) -> None:
        """Initializes the CAN interface.

        Args:
        interface: valid python-can interface
        channel: interface channel
        bitrate: desired bitrate

        """

        assert interface is not None
        assert channel is not None
        assert bitrate != 0

        self._interface = interface
        self._channel = channel
        self._bitrate = bitrate

    def send_recv_frame(self, frame: can.Message, response_id: int) -> bool:
        """Send a frame and read back the response.

        Args:
        frame: can.Message with valid arbitration ID, data and flags
        response_id: The response frame ID

        Following the CAN BAM protocol, the function sends a frame and reads the response off the bus.
        If the response ID matches with the expected ID and the payload is the same (the protocol echoes
        all data), the function returns True.

        Return:
        True/False if response ID matches the provided ID and the payload
        is an echo of the frame payload."""
        with can.interface.Bus(
            bustype=self._interface, channel=self._channel, bitrate=self._bitrate
        ) as bus:
            try:
                bus.send(frame)
            except can.CanError:
                print("Failed to send password!")
                return False

            try:
                resp = bus.recv(1)
                if resp is not None:
                    return (
                        resp.arbitration_id == response_id and resp.data == frame.data
                    )
            except can.CanError:
                print("Failed to receive response!")
                return False

        return False

    def send_password(self, password: int) -> bool:
        """Sends the 8-byte password"""

        assert (
            len(hex(password)) - 2 == 16
        ), "Password lenght is 8 bytes (16 hex digits)"

        pwd = bytearray(password.to_bytes(8, "big"))
        msg = can.Message(
            arbitration_id=ID_SEND_PASSWORD, data=pwd, is_extended_id=False
        )

        return self.send_recv_frame(msg, ID_SEND_PASSWORD_ECHO)

    def send_loading_address(self, code_length: int) -> bool:
        """Sends the VLE bit, the loading address and code size"""

        assert type(code_length) == int, "Code length should be an integer"

        code_length |= 0x80000000
        address_and_size_frame = LOADING_ADDRESS + code_length.to_bytes(4, "big")

        msg = can.Message(
            arbitration_id=ID_SEND_ADDRESS,
            data=address_and_size_frame,
            is_extended_id=False,
        )
        return self.send_recv_frame(msg, ID_SEND_ADDRESS_ECHO)

    def send_code(self, code_length: int, code_bytes: bytes) -> bool:
        """Sends the code to the target"""

        assert type(code_length) == int, "Code length should be an integer"
        assert type(code_bytes) == bytes, "Code should be passed as bytes"

        for i in range(0, code_length, 8):
            msg = can.Message(
                arbitration_id=ID_SEND_DATA,
                data=code_bytes[i : i + 8],
                is_extended_id=False,
            )
            if False == self.send_recv_frame(msg, ID_SEND_DATA_ECHO):
                return False

        return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a RAM image to MPC56xx Boot Assist Module via CAN",
    )

    _create_base_argument_parser(parser)

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    args = parser.parse_args()
    if None == args.password:
        args.password = DEFAULT_PASSWORD

    # Load RAM image to buffer
    ram_image_bytes = ""
    ram_image_len = 0

    with open(args.ram_image, "rb") as f:
        ram_image_bytes = f.read()
        ram_image_len = len(ram_image_bytes)

    # Check if the file is valid
    if 0 == ram_image_len:
        raise ValueError("RAM Image lenght is zero!")

    loader = CANLoader(args.interface, args.channel, args.bitrate)

    assert True == loader.send_password(args.password), 'Failed sending password!'
    assert True == loader.send_loading_address(ram_image_len), 'Failed sending loading address!'
    assert True == loader.send_code(ram_image_len, ram_image_bytes), 'Failed sending image!'


if __name__ == "__main__":
    main()
