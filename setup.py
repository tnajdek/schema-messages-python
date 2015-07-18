try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'name': 'schema-messages',
    'description': '''Simple library that lets you create binary
        representations of arbitrary messages based on a schema
        provided.

        Anticipated for use in applications where identical structure
        messages are transmitted repeatively.
        ''',
    'author': 'Tom Najdek',
    'url': 'https://github.com/tnajdek/schema-messages-python',
    'author_email': 'tom@doppnet.com',
    'version': '0.1',
    'packages': ['message']
}

setup(**config)
