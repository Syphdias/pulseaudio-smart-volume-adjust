#!/usr/bin/env python3
"""Change volume of (preselected) input sink if available
otherwise sink volume will be changed

volume
"""
import re
from argparse import ArgumentParser
from sys import stderr
from typing import Optional

from pulsectl import Pulse, PulseSinkInputInfo


def notify(title: str, text: str) -> None:
    """Use GTK to send notifications"""
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Notify", "0.7")
        from gi.repository import Notify

        Notify.init("smart-volume-adjust")
        n = Notify.Notification.new(title, text)
        n.show()

    except ModuleNotFoundError:
        print(
            "Sorry, something went wrong with the notification. "
            "Are you using Gtk 3.0?",
            file=stderr,
        )


def sink_inputs_filter(
    pulse: Pulse,
    sink_inputs_patterns: list = None,
    verbose: int = 0,
) -> list[PulseSinkInputInfo]:
    """
    Returns filtered list of sinks by list of regexes

    The returned list is prioritised in the order of patterns matching sink inputs
    """
    sink_inputs_filtered = []
    sink_inputs = pulse.sink_input_list()

    for sink_inputs_pattern in sink_inputs_patterns:
        if verbose:
            print(f'Pattern: "{sink_inputs_pattern}"')
        # to only need one iteration over sink_inputs, we need to loop over a copy of the list
        # and keep track of how many elements we have already removed to correct for in in pop()
        removed_count = 0
        for idx, sink_input in enumerate(sink_inputs[:]):
            if re.match(sink_inputs_pattern, pulse.client_info(sink_input.client).name):
                sink_inputs_filtered.append(sink_input)
                sink_inputs.pop(idx - removed_count)
                removed_count += 1
                if verbose:
                    print(
                        f"  sink_input matched: {pulse.client_info(sink_input.client).name}"
                    )
            else:
                if verbose:
                    print(
                        f"  sink_input skipped: {pulse.client_info(sink_input.client).name}"
                    )

    if verbose:
        print("filtered sink inputs:")
        for sink_input in sink_inputs_filtered:
            print(f"  {pulse.client_info(sink_input.client).name}")

    return sink_inputs_filtered


def sink_input_with_sound(
    pulse: Pulse,
    priority_sink_inputs: list,
    verbose: int = 0,
) -> Optional[PulseSinkInputInfo]:
    """Return first sink from list with sound output >0"""
    for sink_input in priority_sink_inputs:
        # using corked here might be a mistake since it might mean
        # that the corked setting is enabled (which is shitty anyways)
        # debug: pacmd list-sink-inputs |grep -e state: -e index: -e client:
        if not sink_input.corked:
            # listen for .09 seconds to sink_input streaming to default sink
            if pulse.get_peak_sample(None, 0.09, sink_input.index):
                return sink_input
    return None


def change_volume(
    pulse: Pulse,
    volume_change: float,
    sink_input: PulseSinkInputInfo = None,
    default_to_sink: bool = False,
    notify_: bool = False,
    verbose: int = 0,
    dry: bool = False,
) -> None:
    """Change volume of given sink input otherwise of sink itself"""
    if sink_input:
        sink_input.volume.value_flat += volume_change
        if not dry:
            pulse.sink_input_volume_set(sink_input.index, sink_input.volume)
        if verbose:
            print(
                "Changing Sink Input Volume for "
                f"{pulse.client_info(sink_input.client).name} by {volume_change:+.2f}",
            )
        if notify_:
            notify(
                "Sink Input Volume",
                f"{volume_change:+.2f} for {pulse.client_info(sink_input.client).name}",
            )

    elif default_to_sink:
        current_sink = pulse.get_sink_by_name(pulse.server_info().default_sink_name)
        current_sink.volume.value_flat += volume_change
        if not dry:
            pulse.sink_volume_set(current_sink.index, current_sink.volume)
        if verbose:
            print(
                "Changing Sink Input Volume for "
                f"{volume_change:+.2f} by {current_sink.description}",
            )
        if notify_:
            notify(
                "Sink Volume",
                f"{volume_change:+.2f} for {current_sink.description}",
            )


def main(args) -> None:
    pulse = Pulse()
    sink_inputs_filtered = sink_inputs_filter(
        pulse,
        args.input_sinks_patterns,
        args.verbose,
    )
    if args.filter_active:
        sink_input_to_change = sink_input_with_sound(
            pulse,
            sink_inputs_filtered,
            args.verbose,
        )
    else:
        if sink_inputs_filtered:
            sink_input_to_change = sink_inputs_filtered[0]
        else:
            sink_input_to_change = None
    change_volume(
        pulse,
        args.volume_change,
        sink_input_to_change,
        args.default_to_sink,
        args.notify,
        args.verbose,
        args.dry_run,
    )


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Change volume of active PulseAudio sink input by given volume.",
    )

    parser.add_argument(
        "volume_change",
        help=(
            "Amount of Volume to change as a float. "
            "Example: -0.05 for lowering volume by 5%"
        ),
    )
    parser.add_argument(
        "input_sinks_patterns",
        nargs="*",
        help=(
            "Supply one or multiple regex patterns to prioritise and filter each sink input "
            "by comparing against input names. "
            'Use "" at the end, if you want to default to any un priorizised sink inputs'
        ),
    )
    parser.add_argument(
        "--default-to-sink",
        action="store_true",
        default=False,
        help="Change volume of default sink if no output was detected on any sink input",
    )
    parser.add_argument(
        "--filter-active",
        action="store_true",
        default=False,
        help="Only consider sink inputs that have been active",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        default=False,
        help="Use Gtk to send a notification which volume was changed and by how much",
    )

    args = parser.parse_args()

    try:
        args.volume_change = float(args.volume_change)
    except ValueError:
        print("volume_change needs to be a number between -1 and 1")
        exit(1)

    main(args)
