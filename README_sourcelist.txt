# MCM Source Report Script

This script collects source information from a list of MCM IP addresses and generates a report on each source’s OTT URL or multicast IP. The report is saved as `MCM_sources.txt` or incrementally named (e.g., `MCM_sources_1.txt`) if the file already exists.

## Prerequisites
- python3
- request library

## Installation and Setup

1. run: pip install requests
2. open config.py and edit the variables

    # config.py
    username = 'Admin'  # Replace with mcm username
    password = 'Admin'  # Replace with mcm password
    ip_addy = ['192.168.86.84', 'IP_ADDRESS_2', 'IP_ADDRESS_3']  # Replace with the list of IP addresses you want to process

3. run: python mcm_source_report.py

4. Script generates a report named MCM_sources.txt
