#!/usr/bin/env python3

# builtins
import os
import sys

# 3rd party
import cherrypy

# mine
try:
    import autopylot
except ImportError:
    sys.path.insert(0, os.path.abspath('.'))
    sys.path.insert(0, os.path.abspath('..'))
    import autopylot


class WebPylot:

    @cherrypy.expose
    def index(self):
        path = os.path.join(os.path.dirname(__file__),
                            "static/html/index.html")
        return open(path)

    # TODO: http://docs.cherrypy.org/en/latest/tutorials.html
    # #tutorial-7-give-us-a-rest

    # EXAMPLE:
    # @cherrypy.expose
    # def generate(self, length=8):
    #     some_string = ''.join(random.sample(string.hexdigits, int(length)))
    #     cherrypy.session['mystring'] = some_string
    #     return some_string
    #
    # @cherrypy.expose
    # def display(self):
    #     return cherrypy.session['mystring']


if __name__ == '__main__':
    static_path = os.path.join(os.path.dirname(__file__), "static/")
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': static_path
        }
    }
    # make it available on each interface (0.0.0.0)
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080,
                            })
    cherrypy.quickstart(WebPylot(), '/', conf)
