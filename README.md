#Schema Messages

[![Build Status](https://travis-ci.org/tnajdek/schema-messages-python.svg?branch=master)](https://travis-ci.org/tnajdek/schema-messages-python)
[![Coverage Status](https://coveralls.io/repos/tnajdek/schema-messages-python/badge.svg?branch=master&service=github)](https://coveralls.io/github/tnajdek/schema-messages-python?branch=master)

Schema Messages creates binary representation of structured data that can be efficiently transmitted over network. Anticipated for use in applications where identical structure messages are transmitted repeatively, e.g. in multiplayer/online games. For example sending the following message:

	{
		'player_id': 42,
		'position_x': 123.45,
		'position_y': 6789.21
	}

Would take 64 bytes to transfer using raw json, 52 bytes using [msgpack](http://msgpack.org/) and only 10 bytes using Schema Messages which would look something like this:

	01 2A 42 F6 E6 66 45 D4 29 AE

However bear in mind that to encode/decode the message on either end, one needs a schema which would look something like this:

	{
			"FrameMessage": {
					"format": {
							"position_x": "float",
							"position_y": "float",
							"player_id": "ubyte"
					 }
			 }
	 }

Schemas **must** be pre-shared on both ends for communication to works.