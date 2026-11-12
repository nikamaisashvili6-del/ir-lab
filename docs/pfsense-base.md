# pfSense base image (one time)

The pfSense installer is interactive and its image can't be redistributed, so this one step is done by hand. Everything after it is code. It only has to be done once, because the result stays on linux F as `ir-lab/base/pfsense-base.qcow2`.

You need the Netgate installer ISO unpacked at `ir-lab/iso/netgate-installer.iso` on linux F. The VM `irlab-pfsense-base` has three network cards, in this order:

| FreeBSD name | Network | Purpose |
|---|---|---|
| `vtnet0` | `irlab-wan` | WAN, has DHCP and internet for the installer |
| `vtnet1` | `irlab-lan` | Lab LAN |
| `vtnet2` | `irlab-mgmt` | Management, from the host |

## Install

1. Open the console: `virt-manager`, then double-click `irlab-pfsense-base`.
2. Accept the licence and choose to install pfSense.
3. When asked for network interfaces, use `vtnet0` as WAN with DHCP. Any LAN choice is fine here, because step 7 replaces it.
4. Choose **pfSense CE** (the free edition). The installer downloads it, which takes a few minutes.
5. Choose the single 8 GB disk, and UFS if it offers a choice.
6. Let it reboot. If it boots back into the installer, shut the VM down, remove the CD in virt-manager, and start it again.

## First-boot console

The console shows a numbered menu once pfSense is up.

7. **Option 1, Assign Interfaces.** No VLANs. WAN = `vtnet0`, LAN = `vtnet2`, no optional interfaces. Using the management card as LAN for now is deliberate: pfSense only allows SSH by default on LAN. The final config puts `vtnet1` back as LAN.
8. **Option 2, Set interface IP.** Choose LAN. IPv4 `10.21.0.1`, subnet bits `24`, no gateway, no IPv6, no DHCP server, and don't revert the web interface to HTTP.
9. **Option 14, Enable Secure Shell.** Answer yes.

## Check it

From the host, this should reach the pfSense menu (password `pfsense`):

```
ssh admin@10.21.0.1
```

Leave the default password alone. The lab's own generated password replaces it when Ansible applies the config.
