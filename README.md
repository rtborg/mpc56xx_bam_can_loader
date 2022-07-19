# MPC56xx Boot Assist Module CAN Loader

MPC56xx family of MCUs have Boot Assist Module (BAM) which allows uploading executable image to RAM. This tools makes use of `socketcan` to send a binary file to a target attached to a CANBus interface.

## How to use

```
python mpc56xx_bam_can_loader.py
```

```
usage: mpc56xx_bam_can_loader.py [-h] [--password PASSWORD] interface channel bitrate ram_image

Send a RAM image to MPC56xx Boot Assist Module via CAN

positional arguments:
  interface            Specify the backend CAN interface to use.
  channel              CAN channel (can0 for example)
  bitrate              Bitrate to use for the CAN bus.
  ram_image            path to RAM image to be loaded to target (.bin format)

optional arguments:
  -h, --help           show this help message and exit
  --password PASSWORD  Target password as 8-byte hex number. Leave blank for using default password.
```

The module can also be installed as a package. It's been tested on Ubuntu 20.04.4 LTS using Microchip CAN Analyzer. 

## References
[Serial BAM Loader](https://github.com/KoblerSystems/mpc55xx-bam-loader-01) from KoblerSystems.