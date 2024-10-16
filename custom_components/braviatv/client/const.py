"""Sony Bravia Client"""
IRCC_DATA = (
"""
<s:Envelope
    xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
    s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:X_SendIRCC xmlns:u="urn:schemas-sony-com:service:IRCC:1">
            <IRCCCode>{}</IRCCCode>
        </u:X_SendIRCC>
    </s:Body>
</s:Envelope>
"""
)

IRCC_HEADERS = {
    "SOAPACTION": '"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"',
}

MINIMUM_UPDATE_INTERVAL = 0

TIMEOUT = 10

VALID_EXT_INPUT_SCHEMES = [
    "extInput:cec",
    "extInput:component",
    "extInput:composite",
    "extInput:hdmi",
    "extInput:widi",
]

VALID_TV_SCHEMES = [
    "tv:analog",
    "tv:atsct",
    "tv:dvbc",
    "tv:dvbs",
    "tv:dvbt",
    "tv:isdbbs",
    "tv:isdbcs",
    "tv:isdbgt",
    "tv:isdbt",
]
