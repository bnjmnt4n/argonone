#!/opt/argonone/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# PEP 8, PEP 263.
"""Argon One Fan and Button Service Daemon."""
import collections
import pathlib
import re
import signal
import subprocess
import time
import typing
import warnings
from threading import Thread

import click
import gpiozero
import smbus2
import toml


_DEFAULT_CONFIG = {
    "fan": {
        "temperatures": [55, 60, 65],
        "speeds": [10, 55, 100],
        "check_temperature_interval": 30,
    },
    "poweroff": {
        # Time in seconds to trigger the action by pressing the shutdown button
        "reboot_range": [1.0, 2.0],
        "shutdown_range": [2.0, 10.0],
        "debounce_time": 0.5,
    },
}

_POWER_BUTTON_GPIO = 4  # GPIO pin that the power button is attached to


def check_shutdown(config: typing.Dict):
    shutdown_button = gpiozero.Button(
        _POWER_BUTTON_GPIO,
        pull_up=False,
        bounce_time=_get_config_option("poweroff", "debounce_time"),
    )

    def on_shutdown_released(device: gpiozero.Button):
        """Check if the shutdown button held long enough to trigger reboot/shutdown."""
        held_time = device.active_time
        # TODO: change to var
        if 2 < held_time < 3:
            subprocess.run("reboot", shell=True)
        elif held_time > 3:
            subprocess.run(["shutdown", "now", "--poweroff"], shell=True)

    shutdown_button.when_released = on_shutdown_released
    signal.pause()  # run until signal received


def get_config(file_name: typing.Union[str, pathlib.Path]) -> typing.Dict:
    path = pathlib.Path(file_name).resolve()
    try:
        return toml.loads(path.read_text())
    except FileNotFoundError:
        warnings.warn(
            "Config file '{}' not found. Using default config.".format(file_name)
        )
        return _DEFAULT_CONFIG


def process_config(config: typing.Dict) -> typing.Dict:
    temperatures = _get_config_option(config, "fan", "temperatures")
    speeds = _get_config_option(config, "fan", "temperatures")
    assert len(temperatures) == len(speeds)
    # Check all temperatures unique
    assert len(temperatures) == len(set(temperatures))
    config["fan"]["temp_speeds"] = collections.OrderedDict(
        sorted(zip(temperatures, speeds))
    )

    for _k, v in _get_config_option(config, "poweroff").items():
        assert len(v) == 2

    return config


def _get_config_option(config: typing.Dict, *args) -> typing.Any:
    value = config
    try:
        # Recurse into config
        for a in args:
            option = value[a]
    except KeyError:
        # Use default value if missing
        value = _DEFAULT_CONFIG
        for a in args:
            value = value[a]
        warnings.warn(
            "Configuration key '{}' not found. Using default value '{}'".format(
                ".".join(args), value
            )
        )

    return value


def _get_temperature() -> float:
    """Get the average of the CPU & GPU temperature."""
    temps = []
    try:
        temps.append(_get_gpu_temperature())
    except subprocess.CalledProcessError:
        temps.append(None)
    try:
        temps.append(_get_cpu_temperature())
    except subprocess.CalledProcessError:
        temps.append(None)
    temps = [t for t in temps if t is not None]
    return sum(temps) / len(temps)


def _get_cpu_temperature() -> float:
    return (
        float(subprocess.check_output(["cat", "/sys/class/thermal/thermal_zone0/temp"]))
        / 1000
    )


def _get_gpu_temperature() -> float:
    """Get the GPU temperature. Close approximation for CPU temperature."""
    # If there's a problem with the regex matching, default to high temperature
    # For safety
    # This must be run as sudo for vcgencmd
    DEFAULT_TEMPERATURE = "100.0"
    temperature_re = re.compile(r"^temp=(.*)'C")
    temp_cmd = subprocess.check_output(["sudo", "vcgencmd", "measure_temp"], stdin=subprocess.DEVNULL)
    temp = float(temperature_re.match(temp_cmd).groups(DEFAULT_TEMPERATURE)[0])
    return temp


def get_fanspeed(temperature: float, temp_speeds: typing.Dict[float, float]):
    max_temp_setting = max((k for k in temp_speeds.keys() if k <= temperature))
    return temp_speeds[max_temp_setting]


def temp_check(config: typing.Dict):
    prevblock = 0

    check_interval = _get_config_option(config, "fan", "check_temperature_interval")
    fanconfig = _get_config_option(config, "fan", "temp_speeds")

    rev = int(gpiozero.pi_info().model[0])
    if rev in {2, 3}:
        bus = smbus2.SMBus(1)
    else:
        bus = smbus2.SMBus(0)

    while True:
        val = _get_gpu_temperature()
        block = get_fanspeed(val, fanconfig)
        if block < prevblock:
            time.sleep(check_interval)
        prevblock = block
        try:
            bus.write_byte_data(0x1A, 0, block)
        except IOError:
            temp = ""
        time.sleep(check_interval)


@click.group()
def cli():
    """Control script to interface with the ArgonOne Raspberry Pi 4 case.

    This script controls the fan speed and shutdown in response to button press.
    """
    pass


@cli.command()
@click.argument("output", type=click.File("w"))
def writeconfig(output: click.File):
    output.write(toml.dumps(_DEFAULT_CONFIG))


@cli.command()
@click.option(
    "--config",
    "config_path",
    default="/etc/argononed.toml",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    envvar="ARGONONE_CONFIG_FILE",
)
def run(config_path: str):
    config_path = pathlib.Path(config_path)
    config = process_config(get_config(config_path))
    try:
        t1 = Thread(target=shutdown_check, args=(config,))
        t2 = Thread(target=temp_check, args=(config,))
        t1.start()
        t2.start()
    finally:
        t1.stop()
        t2.stop()


if __name__ == "__main__":
    cli()
