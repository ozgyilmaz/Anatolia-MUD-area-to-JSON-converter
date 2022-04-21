# Anatolia MUD area to JSON converter
JSON converter for Anatolia Mud area files

Inspired by maplechori's "parse ewar" project.

The project consists of a python file and highly using pyparsing module.

The python script easily converts a standard Anatolia MUD area file to a JSON file.

There are some exceptions and failures:
- social.are is beyond the scope. At least for now...

Usage:

python are-to-json.py <area_name_without_extension>

Example:

python are-to-json.py under2<br/>
python are-to-json.py help<br/>
python are-to-json.py midgaard
