# Dictionary restructured to group expressions by AU type
emotion_primary_patterns = {
    "happiness": [
        ["CheekRaiserL", "CheekRaiserR"],        # AU6 (L or R)
        ["LipCornerPullerL", "LipCornerPullerR"]  # AU12 (L or R)
    ],
    "sadness": [
        ["InnerBrowRaiserL", "InnerBrowRaiserR"],      # AU1 (L or R)
        ["BrowLowererL", "BrowLowererR"],              # AU4 (L or R)
        ["LipCornerDepressorL", "LipCornerDepressorR"]  # AU15 (L or R)
    ],
    "surprise": [
        ["InnerBrowRaiserL", "InnerBrowRaiserR"],      # AU1 (L or R)
        ["OuterBrowRaiserL", "OuterBrowRaiserR"],      # AU2 (L or R)
        ["UpperLidRaiserL", "UpperLidRaiserR"],        # AU5 (L or R)
        ["JawDrop"]                                    # AU26
    ],
    "fear": [
        ["InnerBrowRaiserL", "InnerBrowRaiserR"],      # AU1 (L or R)
        ["OuterBrowRaiserL", "OuterBrowRaiserR"],      # AU2 (L or R)
        ["BrowLowererL", "BrowLowererR"],              # AU4 (L or R)
        ["UpperLidRaiserL", "UpperLidRaiserR"],        # AU5 (L or R)
        ["LipStretcherL", "LipStretcherR"],            # AU20 (L or R)
        ["JawDrop"]                                    # AU26
    ],
    "anger": [
        ["BrowLowererL", "BrowLowererR"],              # AU4 (L or R)
        ["UpperLidRaiserL", "UpperLidRaiserR"],        # AU5 (L or R)
        ["LidTightenerL", "LidTightenerR"],            # AU7 (L or R)
        ["LipTightenerL", "LipTightenerR"],            # AU23 (L or R)
        ["LipPressorL", "LipPressorR"]                 # AU24 (L or R)
    ],
    "disgust": [
        ["NoseWrinklerL", "NoseWrinklerR"],            # AU9 (L or R)
        ["UpperLipRaiserL", "UpperLipRaiserR"],        # AU10 (L or R)
        ["LipCornerDepressorL", "LipCornerDepressorR"],# AU15 (L or R)
        ["LowerLipDepressorL", "LowerLipDepressorR"],  # AU16 (L or R)
        ["ChinRaiserB", "ChinRaiserT"]                 # AU17
    ],
}