# Disable CPU Cores
A Python script to modify Nexus 5X boot images to disable big CPU core in order to workaround the bootloop of death (BLOD). The original fix was found by XCnathan32.

This script has been created to simplify the process of creating new boot images for every new security update. In addition, security-conscious people who do not like to download random kernel images from the Internet can use this script to create a fixed image based on the official factory image.

References:
 - XDA Thread: https://forum.xda-developers.com/nexus-5x/general/untested-nexus-5x-bootloop-death-fix-t3641199
 - Original changes: https://github.com/xcnathan32/4Core-Android-O-5X/commit/a4814e7e9c05e09d41ad1621f9d95f7eea409d77

This script requires Python 2.7 or Python 3. It has been tested on Nexus 5X Oreo (OPR4.170623.009) boot and recovery images.

## Usage
Run this script in order to generate new boot and recovery images
```
./disable_cpu_cores.py --disable-encryption boot.img new_boot.img
./disable_cpu_cores.py --disable-encryption recovery.img new_recovery.img
```

The `--disable-encryption` flag is optional and can be used to disabled forced disk encryption.

After that, use `fastboot` to flash the new boot images to your device.
```
fastboot flash boot new_boot.img
fastboot flash recovery new_recovery.img
```
