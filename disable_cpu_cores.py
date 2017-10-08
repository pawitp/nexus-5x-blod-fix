#!/usr/bin/python

import struct
import argparse
import gzip
import io
from collections import namedtuple

# See system/core/mkbootimg/bootimg.h
BOOT_MAGIC_SIZE = 8
BOOT_NAME_SIZE = 16
BOOT_ARGS_SIZE = 512
BOOT_EXTRA_ARGS_SIZE = 1024
HEADER_STRUCT = '<8sIIIIIIIIII16s512s32s1024s'
ImageHeader = namedtuple('ImageHeader', 'magic, kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size, second_addr, tags_addr, page_size, unused, os_version, name, cmdline, id, extra_cmdline')
Image = namedtuple('Image', 'header, kernel, ramdisk, second')

# Strings to replace inside ramdisk (each pair must have equal size because we do not parse the cpio format)
REPLACE_STRINGS = [
  (
    b'write /dev/cpuset/foreground/cpus 0-2,4-5',
    b'write /dev/cpuset/foreground/cpus 0-3    '
  ),
  (
    b'write /dev/cpuset/foreground/boost/cpus 4-5',
    b'write /dev/cpuset/foreground/boost/cpus 0-3'
  ),
  (
    b'write /dev/cpuset/background/cpus 0',
    b'write /dev/cpuset/background/cpus 3'
  ),
  (
    b'write /dev/cpuset/system-background/cpus 0-2',
    b'write /dev/cpuset/system-background/cpus 2-3'
  ),
  (
    b'write /dev/cpuset/top-app/cpus 0-5',
    b'write /dev/cpuset/top-app/cpus 0-3'
  )
]

REPLACE_ENCRYPTION = [
  (
    b',verify=/dev/block/platform/soc.0/f9824900.sdhci/by-name/metadata',
    b'                                                                 '
  ),
  (
    b',forcefdeorfbe=/dev/block/platform/soc.0/f9824900.sdhci/by-name/metadata',
    b'                                                                        '
  )
]

def main():
  parser = argparse.ArgumentParser(description='Modifies a Nexus 5X boot or recovery image to disable big cores.')
  parser.add_argument('input', type=str, help='input file')
  parser.add_argument('output', type=str, help='output file')
  parser.add_argument('--disable-encryption', action='store_true', help='disable encryption and verified boot')
  args = parser.parse_args()
  
  with open(args.input, 'rb') as infile:
    original_content = infile.read()

  header = ImageHeader._make(struct.unpack_from(HEADER_STRUCT, original_content))
  
  # Round up to nearest page size
  def pad_size(original_size):
    return ((original_size + header.page_size - 1) // header.page_size) * header.page_size
  
  image_struct = '<%ds%ds%ds%ds' % (header.page_size, pad_size(header.kernel_size), pad_size(header.ramdisk_size), pad_size(header.second_size))
  image = Image._make(struct.unpack_from(image_struct, original_content))
  
  # Modify cmdline
  header = header._replace(cmdline=modify_cmdline(header.cmdline))
  
  # Modify ramdisk
  replace_strings = REPLACE_STRINGS
  if args.disable_encryption:
    replace_strings = replace_strings + REPLACE_ENCRYPTION

  image = image._replace(ramdisk=compress(modify_ramdisk(uncompress(image.ramdisk), replace_strings)))
  header = header._replace(ramdisk_size=len(image.ramdisk))
  
  # Generate new header
  image = image._replace(header=struct.pack(HEADER_STRUCT, *header))
  
  # Generate new image
  image_struct = '<%ds%ds%ds%ds' % (header.page_size, pad_size(header.kernel_size), pad_size(header.ramdisk_size), pad_size(header.second_size))
  new_image = struct.pack(image_struct, *image)
  
  with open(args.output, 'wb') as outfile:
    outfile.write(new_image)

# Strip garbage from null-terminated string
def strip(input):
  return input.partition(b'\0')[0]

# Modify cmdline to use 4 CPUs
def modify_cmdline(cmdline):
  original_cmdline = strip(cmdline)
  new_cmdline = cmdline.replace(b'boot_cpus=0-5', b'boot_cpus=0-3 maxcpus=4')
  print("Original cmdline: " + cmdline.decode('ascii'))
  print("Modified cmdline: " + new_cmdline.decode('ascii'))

  return new_cmdline

# Modify ramdisk which will override cmdline when booted
def modify_ramdisk(ramdisk, replace_strings):
  for (search, replace) in replace_strings:
    if ramdisk.find(search) >= 0:
      print("Found   : " + search.decode('ascii'))
      print("Replaced: " + replace.decode('ascii'))
      ramdisk = ramdisk.replace(search, replace)
    else:
      print("Not Found: " + search.decode('ascii'))

  return ramdisk

# Gunzip string
def uncompress(gzip_string):
  with gzip.GzipFile(fileobj=io.BytesIO(gzip_string)) as f:
    return f.read()

def compress(plain_string):
  out = io.BytesIO()
  with gzip.GzipFile(fileobj=out, mode='wb', mtime=0) as f:
    f.write(plain_string)
  return out.getvalue()


if __name__ == "__main__":
    main()
