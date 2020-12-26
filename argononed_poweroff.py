#!/opt/argonone/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# PEP 8, PEP 263.
"""Argon One (Raspberry Pi 4B) Systemd Shutdown script."""
import click
import gpiozero
import smbus2


@click.command()
@click.argument(
    "shutdown_type",
    default="poweroff",
    type=click.Choice(["poweroff", "halt", "reboot", "kexec"], case_sensitive=False),
)
def cli(shutdown_type: str):
    rev = int(gpiozero.pi_info().model[0])
    if rev in {2, 3}:
        bus = smbus2.SMBus(1)
    else:
        bus = smbus2.SMBus(0)

    bus.write_byte_data(0x1A, 0, 0)
    if shutdown_type.lower() in {"poweroff", "halt"}:
        try:
            bus.write_byte_data(0x1A, 0, 0xFF)
        except:
            warnings.warn("Could not set LED OFF")


if __name__ == "__main__":
    cli()
