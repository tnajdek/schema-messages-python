try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

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
    'version': '0.1.1',
    'packages': ['schemamessages'],
    'install_requires': ['future', 'bidict']
}

setup(**config)
