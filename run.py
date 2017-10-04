#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gerritviewer import app

app = app.create_app('config')
if __name__ == '__main__':
    app.run()
