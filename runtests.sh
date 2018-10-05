#!/bin/bash

nosetests -s --nologcapture --ckan --with-pylons=test-local.ini $@
