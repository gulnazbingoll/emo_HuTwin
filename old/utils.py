# Dizionario che mappa ogni emozione principale alle sue AU specifiche (pattern primario)
emotion_primary_patterns = {
    "happiness": [
        "CheekRaiserL",
        "CheekRaiserR",  # AU6
        "LipCornerPullerL",
        "LipCornerPullerR",  # AU12
    ],
    "sadness": [
        "InnerBrowRaiserL",
        "InnerBrowRaiserR",  # AU1
        "BrowLowererL",
        "BrowLowererR",  # AU4
        "LipCornerDepressorL",
        "LipCornerDepressorR",  # AU15
    ],
    "surprise": [
        "InnerBrowRaiserL",
        "InnerBrowRaiserR",  # AU1
        "OuterBrowRaiserL",
        "OuterBrowRaiserR",  # AU2
        "UpperLidRaiserL",
        "UpperLidRaiserR",  # AU5
        "JawDrop",  # AU26
    ],
    "fear": [
        "InnerBrowRaiserL",
        "InnerBrowRaiserR",  # AU1
        "OuterBrowRaiserL",
        "OuterBrowRaiserR",  # AU2
        "BrowLowererL",
        "BrowLowererR",  # AU4
        "UpperLidRaiserL",
        "UpperLidRaiserR",  # AU5
        "LipStretcherL",
        "LipStretcherR",  # AU20
        "JawDrop",  # AU26
    ],
    "anger": [
        "BrowLowererL",
        "BrowLowererR",  # AU4
        "UpperLidRaiserL",
        "UpperLidRaiserR",  # AU5
        "LidTightenerL",
        "LidTightenerR",  # AU7
        "LipTightenerL",
        "LipTightenerR",  # AU23
        "LipPressorL",
        "LipPressorR",  # AU24
    ],
    "disgust": [
        "NoseWrinklerL",
        "NoseWrinklerR",  # AU9
        "UpperLipRaiserL",
        "UpperLipRaiserR",  # AU10
        "LipCornerDepressorL",
        "LipCornerDepressorR",  # AU15
        "LowerLipDepressorL",
        "LowerLipDepressorR",  # AU16
        "ChinRaiserB",
        "ChinRaiserT",  # AU17
    ],
}
