#!/usr/bin/python
########################################################################################################################
# Author:   Jordan Thompson
# Email:    Jordan@ThompCo.com
#
# GNU General Public Licence:
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################################################################

import os.path
import pycurl
import sys
from StringIO import StringIO
import smtplib
import email
import ConfigParser

############################################################
# this file is installed in /root/bin
# the crontab entry (crontab -e) looks something like this:
# 0 * * * * /root/bin/CheckIp.py
############################################################

IP_FILE = "old_ip.txt"
CONFIG_FILE = "CheckIp.ini"
EMAIL_SECTION = "Email"
MESSAGE_SECTION = "Message"
OLD_IP_ADDRESS_DESIGATOR = "%OLD_IP_ADDRESS%"
NEW_IP_ADDRESS_DESIGATOR = "%NEW_IP_ADDRESS%"


########################################################################################################################
# Reads the configuration file and returns:
# the contents of the config file in a config structure
########################################################################################################################
def read_config_file(config_file_name):
    config = ConfigParser.RawConfigParser()
    config.read(config_file_name)
    return config


########################################################################################################################
# Gets the current IP of the router and returns:
# ip_address:   current IP address of the router
########################################################################################################################
def get_current_ip():
    string_buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, "http://checkip.dyndns.org")
    c.setopt(c.WRITEFUNCTION, string_buffer.write)
    c.perform()
    c.close()
    body = string_buffer.getvalue()
    ip_address = body.split("IP Address:")[1].split("<")[0].strip()
    return ip_address


########################################################################################################################
# Gets the old IP address or None if invalid from the save-file and returns:
# ip_address:   old IP address or None
########################################################################################################################
def get_old_ip():
    if os.path.isfile(IP_FILE):
        f = open(IP_FILE, 'r')
        ip_address = f.read().strip()
        f.close()
        check = ip_address.split(".")
        try:
            if len(check) == 4:
                for i in check:
                    x = int(i)
                    if x > 254 or x == 0:
                        raise ValueError("Invalid value: '" + str(i) + "'")
            else:
                raise ValueError("Invalid IP address: '" + str(ip_address) + "'")
        except ValueError:
            os.remove(IP_FILE)
            ip_address = None
    else:
        ip_address = None
    return ip_address


########################################################################################################################
# Saves the ip address to a file
# ip_address:   the address to save
########################################################################################################################
def save_current_ip(ip_address):
    f = open(IP_FILE, 'w')
    f.write(ip_address)
    f.close()


########################################################################################################################
# sends the mail to the user
# config:       the contents of the config file in a config structure
# old_address:  the old IP address to include in the message
# new_address:  the new IP address to include in the message
########################################################################################################################
def send_mail(config, old_address, new_address):
    msg = email.MIMEMultipart.MIMEMultipart()
    email_from = config.get(EMAIL_SECTION, "FROM")
    email_to = config.get(EMAIL_SECTION, "TO")
    msg['From'] = email_from
    msg['To'] = email_to
    if old_address is None:
        old_address = "Not found"
    msg['Subject'] = config.get(MESSAGE_SECTION, "SUBJECT").replace(OLD_IP_ADDRESS_DESIGATOR, old_address)\
        .replace(NEW_IP_ADDRESS_DESIGATOR, new_address)
    body = config.get(MESSAGE_SECTION, "BODY").replace(OLD_IP_ADDRESS_DESIGATOR, old_address)\
        .replace(NEW_IP_ADDRESS_DESIGATOR, new_address)
    msg.attach(email.MIMEText.MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_from, config.get(EMAIL_SECTION, "PASSWORD"))
    text = msg.as_string()
    server.sendmail(email_from, email_to, text)
    server.quit()

########################################################################################################################
# main function
# Opens the config file and the save-file (if it exists)
# Gets the current router IP address
# Compares the current IP address with the previous one.
# If different, it updates the save-file and emails the message
# If the same, exits
########################################################################################################################
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print sys.argv[0] + " requires only one parameter which should be the configuration file"
        exit(1)
    config = read_config_file(sys.argv[1])
    new_ip_address = get_current_ip()
    old_ip_address = get_old_ip()
    if old_ip_address != new_ip_address:
        save_current_ip(new_ip_address)
        send_mail(config, old_ip_address, new_ip_address)
