## About
This script changed the volume of either the active PulseAudio sink or the
active PulseAudio sink input. Documentation (and FAQ – if any) is found in
this README.

- There is currently no package to install the script.
  You need to download it from [here](
  https://raw.githubusercontent.com/Syphdias/pulseaudio-smart-volume-adjust/main/smart-volume-adjust.py)
  Or clone the repository.
- Feel free to file issues to report bugs, ask questions,
  or request features.
- Feel free to open a pull request. Please use the [black](
  https://github.com/psf/black) code formatter.

## Install requirements
```
pip install --user -r requirements.txt
```
For notifications GTK4 is prerequisite. The above command will not install it.
Please use your operating systems means to do so.

## Usage
The following example shows most options I would expect to get used when using
the script. You can also use `--help` to show the available parameters.

```sh
smart-volume-adjust.py \
    --filter-active --default-to-sink --notify --notify-absolute \
    +.05 "Spotify" "Google Chrome" ""
```

This will pick the first sink input playing sound (`--filter-active`) that
matches the regex patterns "Spotify", "Google Chrome", or any other sink input
playing sound (`""`).
If no sink input is found that plays sound and matches one of the regex
patterns, the default sink will be used (`--default-to-sink`).
The picked sink input or sink will then be increased by 5% (`+0.05`, the "+" is
optional for increasind volume).
A message will be shown with which sink or sink input was changed and by how
much (`--notify`). In this case instead of the relative change the current
volume will be shown (`--notify-abolute`).


The option `--default-to-sink` only makes sense together with the option
`--filter-active`.


## Finding Sink Input Names

To find a good regex pattern you can use the following command that does not
change volume of any sink input, has a regex pattern that matches everything,
and shows what was matched by the regex patterns.

```sh
smart-volume-adjust.py --dry-run -v -.001 "Test" ""
```
