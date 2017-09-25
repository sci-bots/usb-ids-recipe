import argparse
import path_helpers as ph
import platform
import re
import sys

import bz2
import json


def parse_usb_ids_list(data):
    '''
    Parse list of USB vendor/product IDs in format used by:

        http://www.linux-usb.org/usb.ids

    Parameters
    ----------
    data : str
        Text list of USB vendor/product IDs in format used by:

            http://www.linux-usb.org/usb.ids

    Returns
    -------
    dict
        Returns two-level dictionary.

        First level is keyed by vendor ID.  Vendor items contain ``name`` key,
        and also contain ``products`` key if any products are parsed for the
        vendor.
    '''
    cre_vendor = re.compile(r'^(?P<vendor_id>[a-fA-F0-9]+)\s+'
                            r'(?P<vendor_name>.*)$')
    cre_product = re.compile(r'^\s+(?P<product_id>[a-fA-F0-9]+)\s+'
                             r'(?P<product_name>.*)$')

    usb_ids = {}
    vendor_j = None

    for line_i in data.strip().splitlines():
        match_i = cre_vendor.match(line_i)
        if match_i:
            vendor_j = {'name': match_i.group('vendor_name')}
            usb_ids[match_i.group('vendor_id')] = vendor_j
            continue

        match_i = cre_product.match(line_i)
        if match_i and vendor_j is not None:
            products_j = vendor_j.get('products', {})
            products_j[match_i.group('product_id')] =\
                {'name': match_i.group('product_name')}
            vendor_j['products'] = products_j
            continue
    return usb_ids


def parse_args(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Text file containing USB '
                        'vendor/product IDs in format used by: '
                        'http://www.linux-usb.org/usb.ids')
    parser.add_argument('output_file', help='Output path for JSON (default: '
                        'stdout)', default='-')
    parser.add_argument('-z', '--compress', help='Compress output to bz2',
                        action='store_true')
    parsed_args = parser.parse_args(args=args)

    if parsed_args.output_file[-4:].lower() == '.bz2':
        parsed_args.compress = True
    return parsed_args


def main(args=None):
    args = parse_args(args=args)

    with open(args.input_file, 'r') as input_:
        usb_ids = parse_usb_ids_list(input_.read())

    usb_ids_json = json.dumps(usb_ids, indent=2)

    if args.output_file == '-':
        print usb_ids_json,
    else:
        if args.compress:
            mode = 'wb'
            usb_ids_json = bz2.compress(usb_ids_json)
        else:
            mode = 'w'

        with open(args.output_file, mode) as output_:
            output_.write(usb_ids_json)


if __name__ == '__main__':
    import os

    src_dir = ph.path(os.environ['RECIPE_DIR'])
    input_file = src_dir.joinpath('usb.ids')

    # On Windows, Unix-style packages are [installed to `LIBRARY_PREFIX`][1].
    #
    # [1]: https://conda.io/docs/user-guide/tasks/build-packages/environment-variables.html#environment-variables-set-during-the-build-process
    LIBRARY_PREFIX = ph.path(os.environ['LIBRARY_PREFIX']
                             if platform.system() == 'Windows'
                             else os.environ['PREFIX'])

    output_dir = LIBRARY_PREFIX.joinpath('share', 'usb-ids')
    output_dir.makedirs_p()

    # Copy source file to output directory.
    input_file.copy(output_dir.joinpath(input_file.name))

    # Write JSON formatted file to output directory.
    output_file = output_dir.joinpath('usb-ids.json.bz2')

    main(args=[input_file, output_file])
