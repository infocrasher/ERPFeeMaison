import usb.core
import usb.util
import time

# Trouver l’imprimante
dev = usb.core.find(idVendor=0x0471, idProduct=0x0055)

if dev is None:
    raise ValueError("Imprimante non détectée")

# Détacher le driver système si nécessaire
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)

# Sélectionner la configuration et l'interface
dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0,0)]

# Chercher l’endpoint OUT
ep_out = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
)

# Message test ESC/POS
message = b"\x1b@\nTEST IMPRIMANTE GPRINTER\n\n\x1dVAU REUSSI!\n\n\x1b@\n\n\n"

# Envoyer
ep_out.write(message)

print("✅ Impression test envoyée.")
time.sleep(1)
