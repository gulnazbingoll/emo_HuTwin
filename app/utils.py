# Dizionario ristrutturato che raggruppa le espressioni per tipo di AU
emotion_primary_patterns = {
    "happiness": [
        ["CheekRaiserL", "CheekRaiserR"],        # AU6 (L o R)
        ["LipCornerPullerL", "LipCornerPullerR"]  # AU12 (L o R)
    ],
    "sadness": [
        ["InnerBrowRaiserL", "InnerBrowRaiserR"],      # AU1 (L o R)
        ["BrowLowererL", "BrowLowererR"],              # AU4 (L o R)
        ["LipCornerDepressorL", "LipCornerDepressorR"]  # AU15 (L o R)
    ],
    "surprise": [
        ["InnerBrowRaiserL", "InnerBrowRaiserR"],      # AU1 (L o R)
        ["OuterBrowRaiserL", "OuterBrowRaiserR"],      # AU2 (L o R)
        ["UpperLidRaiserL", "UpperLidRaiserR"],        # AU5 (L o R)
        ["JawDrop"]                                    # AU26
    ],
    "fear": [
        ["InnerBrowRaiserL", "InnerBrowRaiserR"],      # AU1 (L o R)
        ["OuterBrowRaiserL", "OuterBrowRaiserR"],      # AU2 (L o R)
        ["BrowLowererL", "BrowLowererR"],              # AU4 (L o R)
        ["UpperLidRaiserL", "UpperLidRaiserR"],        # AU5 (L o R)
        ["LipStretcherL", "LipStretcherR"],            # AU20 (L o R)
        ["JawDrop"]                                    # AU26
    ],
    "anger": [
        ["BrowLowererL", "BrowLowererR"],              # AU4 (L o R)
        ["UpperLidRaiserL", "UpperLidRaiserR"],        # AU5 (L o R)
        ["LidTightenerL", "LidTightenerR"],            # AU7 (L o R)
        ["LipTightenerL", "LipTightenerR"],            # AU23 (L o R)
        ["LipPressorL", "LipPressorR"]                 # AU24 (L o R)
    ],
    "disgust": [
        ["NoseWrinklerL", "NoseWrinklerR"],            # AU9 (L o R)
        ["UpperLipRaiserL", "UpperLipRaiserR"],        # AU10 (L o R)
        ["LipCornerDepressorL", "LipCornerDepressorR"],# AU15 (L o R)
        ["LowerLipDepressorL", "LowerLipDepressorR"],  # AU16 (L o R)
        ["ChinRaiserB", "ChinRaiserT"]                 # AU17
    ],
}