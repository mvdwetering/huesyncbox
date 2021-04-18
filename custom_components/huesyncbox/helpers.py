"""Helpers for the Philips Hue Play HDMI Sync Box integration."""

import textwrap


def redacted(value):
    """ Returns a consistent redacted value for the given input """
    try:
        return redacted.values[value]
    except AttributeError:
        redacted.values = {}
    except KeyError:
        pass

    redacted_value = f"redacted_{len(redacted.values.items()) + 1}"
    redacted.values[value] = redacted_value

    return redacted_value


def log_entry_data(data):
    output = ""
    output += f"name: {data['name']}\n"
    output += f"host: {data['host']}\n"
    output += f"port: {data['port']}\n"
    output += f"path: {data['path']}\n"
    output += f"reg: {data['registration_id'] if 'registration_id' in data else None}\n"
    output += f"devicetype: {data['devicetype'] if 'devicetype' in data else None}\n"
    output += f"uid: {redacted(data['unique_id'])}\n"
    output += (
        f"token: {redacted(data['access_token']) if 'access_token' in data else None}\n"
    )

    return output


def log_config_entry(entry):
    output = ""
    output += f"entry_id: {entry.entry_id}\n"
    output += f"uid: {redacted(entry.unique_id)}\n"
    output += f"data:\n{textwrap.indent(log_entry_data(entry.data), '  ')}\n"

    return output
