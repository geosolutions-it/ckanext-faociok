#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import json
import argparse



def get_parser():
    p = argparse.ArgumentParser(prog='csv2json')
    p.add_argument('source', help="Source csv file")
    p.add_argument('destination', help="Target directory")
    return p

def main():
    p = get_parser()
    args = p.parse_args()
    with open(args.source, 'rt') as from_file:
        r = csv.reader(from_file)
        header = list(r.next())

        for row in r:
            data = dict(zip(header, row))
            fname = os.path.join(args.destination, '{}.json'.format(data[header[0]]))

            with open(fname, 'wt') as to_file:
                json.dump(data, to_file)

if __name__ == '__main__':
    main()
