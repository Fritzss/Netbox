#!/usr/bin/python3
import pynetbox
import ipaddress
from subprocess import getstatusoutput as getst
import time
from multiprocessing import Pool

# connect to Netbox
nb = pynetbox.api('https://<netbox url>:443', token='<netbox token>')
nb.http_session.verify = False
# Get all Prefixes
prefixes = nb.ipam.prefixes.all()
# Exclude subnet
prefixes = [net for net in prefixes if 'xxx.xxx.' not in str(net)]
# Create array all IP addresses
addrs = ''
for net in prefixes:
    for addr in ipaddress.IPv4Network(net):
        addrs += ' ' + (str(addr))
addrs = addrs.split(' ')


# add ip to Netbox
def addnb(addr):
    respon = ''
    try:
        ip_update = nb.ipam.ip_addresses.get(address=addr)
        if ip_update is None:
            respon = nb.ipam.ip_addresses.create(address=addr, vrf=1, description='add by pinger')
        elif str(ip_update.status).lower() == 'deprecated' or str(ip_update.status).lower() == 'reserved':
            date = dict(status='active', description=time.ctime())
            respon = ip_update.update(date)
    except Exception as e:
        respon = e
    return respon


# Change status if ip not avalible
def disable_ip(addr):
    respon = ''
    try:
        ip_update = nb.ipam.ip_addresses.get(address=addr)
        if ip_update is not None and str(ip_update.status).lower() != 'deprecated' and str(
                ip_update.status).lower() != 'reserved':
            data = dict(status='deprecated', description=f'Update {time.ctime()}')
            respon = ip_update.update(data)
        elif ip_update is None:
            respon = nb.ipam.ip_addresses.create(address=addr, vrf=1, description='add by pinger', status='reserved')
    except Exception as e:
        respon = e
    return respon


# Check IP and add or disable in Netbox
def pinger(addr):
    status, result = getst('/usr/bin/ping -c1 ' + str(addr))
    if status == 0:
        addnb(addr)
    else:
        disable_ip(addr)


# start async ipscann
if __name__ == '__main__':
    pool = Pool(255)
    pool.map(pinger, addrs)
    pool.close()
    pool.join()
