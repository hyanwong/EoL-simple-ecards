# EoL-simple-ecards
A simple ecards script of the Encyclopaedia of Life

This is a single perl script that mines http://eol.org for images (public domain or cc-by) and allows a visitor to 
'send' an e-card of that image, with a message.

In fact, no sending is done by the server. The script simply constructs a mailto:url with a link, in which is embedded 
the message and the image ID, in a simple ROT13 encoding. Anyone visiting the url specified in the mailto link will see 
the image and the message.

This avoids having to run a mail server, which can be open to abuse by spammers, etc.

The 2 security concerns are:

1) Visitors can specify a message which gets displayed on a server page. So we need to make sure they can't embed malicious html, to carry out cross-site scripting attacks
2) Even in plain text, visitors can send an offensive message, which would get displayed on the page by anyone with the link (although the message is, in fact, embedded in the link, rather than stored on the server)

(1) can be solved easily. (2) is essentially impossibly to monitor, so the ecard page should be appropriately worded.
