from distutils.core import setup
from distutils.extension import Extension

try:
    from Cython.Distutils import build_ext
except ImportError:
    use_cython = False
else:
    use_cython = True

cmdclass = {}
ext_modules = []

if use_cython:
    ext_modules += [
        Extension("schemamessages.exceptions", [ "schemamessages/exceptions.pyx" ]),
        Extension("schemamessages.factory", [ "schemamessages/factory.pyx" ]),
        Extension("schemamessages.message", [ "schemamessages/message.pyx" ]),
        Extension("schemamessages.packers", [ "schemamessages/packers.pyx" ]),
        Extension("schemamessages.unpackers", [ "schemamessages/unpackers.pyx" ]),
        Extension("schemamessages.utils", [ "schemamessages/utils.pyx" ]),
    ]
    cmdclass.update({ 'build_ext': build_ext })
else:
    ext_modules += [
        Extension("schemamessages.exceptions", [ "schemamessages/exceptions.c" ]),
        Extension("schemamessages.factory", [ "schemamessages/factory.c" ]),
        Extension("schemamessages.message", [ "schemamessages/message.c" ]),
        Extension("schemamessages.packers", [ "schemamessages/packers.c" ]),
        Extension("schemamessages.unpackers", [ "schemamessages/unpackers.c" ]),
        Extension("schemamessages.utils", [ "schemamessages/utils.c" ]),
    ]

config = {
    'name': 'schema-messages',
    'description': 'Library to create network-efficient binary representations of structured data.',
    'long_description': '''Schema Messages creates binary representation of
        structured data that can be efficiently transmitted over network.
        Anticipated for use in applications where identical structure messages
        are transmitted repeatively, e.g. in multiplayer/online games.''',
    'license': 'MIT',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    'author': 'Tom Najdek',
    'url': 'https://github.com/tnajdek/schema-messages-python',
    'author_email': 'tom@doppnet.com',
    'version': '0.1.11',
    'packages': ['schemamessages'],
    'install_requires': ['future', 'bidict']
}

setup(cmdclass = cmdclass, ext_modules=ext_modules, **config)
