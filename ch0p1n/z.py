"""
Elaborate and repeat (vary) motifs.
"""

from typing import Union, List, Optional, Dict, Tuple, Any
from copy import deepcopy
from itertools import product

Pitch = int
PitchClass = int
PitchLine = List[Union[Pitch, None, List[Pitch]]]

# the term "pitch line" denotes the pitch content of musical line
# the same goes for "duration line"

Duration = Union[int, float]
DurationLine = List[Duration]



# move single pitches ------------------------------------------

def _reify(scale: List[PitchClass]) -> List[Pitch]:

    """
    Turn a scale into its whole range of pitches.
    """

    scale.sort()

    pitches = [
        pitch_class + octave*12
        for octave in range(11)
        for pitch_class in scale
    ]

    return pitches


def _move(
        pitch: Optional[Pitch],
        scale: List[Pitch], # reified
        step: int
    ) -> Optional[Pitch]:

    """
    Move a pitch along a scale by certain number of steps.
    """

    if pitch is None:
        return None

    if pitch not in scale:
        if step == 0:
            # rather than trigger an error
            return None
        else:
            # insert `pitch` into `scale`
            scale.append(pitch)
            scale.sort()

    i = scale.index(pitch)

    # move `pitch`
    pitch = scale[i + step]

    return pitch


def _move2(
        pitch: Optional[Pitch],
        scale: List[Pitch],
        steps: List[int]
    ) -> List[Optional[Pitch]]:

    """
    Move a pitch along a scale by different numbers of steps.
    """

    if pitch is None:
        return [None]

    if (pitch not in scale) and (0 in steps):
        steps = [step for step in steps if step != 0]
        # `steps` may be empty now,
        # so the next clause must be after this one

    if not steps:
        return []

    pitches = [_move(pitch, scale, step) for step in steps]
    return pitches



# extract and replace pitches ----------------------------------

def _extract(pitch_motif: PitchLine) -> List[Optional[Pitch]]:

    """
    Extract pitches from a pitch motif.
    """

    pitches = []

    for item in pitch_motif:
        if isinstance(item, list):
            pitches.extend(item)
        else:
            pitches.append(item)

    return pitches


def _replace(
        pitch_motif: PitchLine,
        pitches: List[Optional[Pitch]],
        in_place: bool = False
    ) -> Optional[PitchLine]:

    """
    Replace the pitches of a motif.
    """

    if not in_place:
        pitch_motif = deepcopy(pitch_motif)

    k = 0

    for i, item in enumerate(pitch_motif):
        if isinstance(item, list):
            l = len(item)
            pitch_motif[i] = pitches[k:k+l]
            k = k + l
        else:
            pitch_motif[i] = pitches[k]
            k = k + 1

    if not in_place:
        return pitch_motif



# repeat pitch motifs ------------------------------------------

def rescale(
        pitch_motif: PitchLine,
        mapping: Dict[PitchClass, PitchClass]
    ) -> PitchLine:
    
    """
    Map the pitches of a pitch motif onto a new scale.
    """

    pitches = _extract(pitch_motif)

    # map `pitches`
    for i, pitch in enumerate(pitches):
        if pitch is None:
            continue

        octave = pitch // 12
        pitch_class = pitch % 12

        if pitch_class not in mapping:
            continue

        to = mapping[pitch_class]

        # get the nearest pitch
        # for example, for mapping `{11: 0}` and pitch 59,
        # the resulted pitch should be 60 rather than 48
        d = to - pitch_class

        if d >= 6:
            to = to - 12
        elif d <= -6:
            to = to + 12

        pitches[i] = to + octave*12

    motif = _replace(pitch_motif, pitches)
    return motif


def transpose(
        pitch_motif: PitchLine,
        scale: List[PitchClass],
        step: int
    ) -> PitchLine:

    """
    Transpose a pitch motif along a given scale
    by a certain number of steps.
    """
    
    scale = _reify(scale)
    pitches = _extract(pitch_motif)

    pitches = [
        _move(pitch, scale, step)
        for pitch in pitches
    ]

    motif = _replace(pitch_motif, pitches)
    return motif


def lead(
        pitch_motif: PitchLine,
        harmony: List[PitchClass],
        steps: List[int] = [-1, 0, 1],
        complete: bool = True
    ) -> List[PitchLine]:
    
    """
    Repeat a pitch motif in a given harmony,
    according to the common tone rule and nearest chordal tone rule.
    """
    
    pitches = _extract(pitch_motif)

    # get each pitch's nearest pitches
    nearest_pitches = [
        _move2(pitch, harmony, steps)
        for pitch in pitches
    ]

    # combine pitches
    pitch_groups = product(*nearest_pitches)

    if complete:
        pitch_groups = [
            pitch_group if _is_complete(pitch_group, harmony)
            for pitch_group in pitch_groups
        ]

    # generate motifs
    motifs = [
        # note that `pitch_group` is tuple
        _replace(pitch_motif, list(pitch_group))
        for pitch_group in pitch_groups
    ]

    return motifs



# modify and access pitches ------------------------------------

def _modify(
        pitch_motif: PitchLine,
        position: Union[int, Tuple[int, int]],
        item: Any,
        in_place: bool = False
    ) -> Optional[PitchLine]:

    """
    Change the item of a pitch motif at the given position.
    """

    if not in_place:
        pitch_motif = deepcopy(pitch_motif)

    if isinstance(position, int):
        pitch_motif[position] = item
    else:
        i, j = position
        pitch_motif[i][j] = item

    if not in_place:
        return pitch_motif


def _access(
        pitch_motif: PitchLine,
        position: Union[int, Tuple[int, int]]
    ) -> Union[Pitch, None, List[Pitch]]:
    
    """
    Get the item at the given position from a pitch motif.
    """

    if isinstance(position, int):
        item = pitch_motif[position]
    else:
        i, j = position
        item = pitch_motif[i][j]
    
    return item



# select pitch motifs ------------------------------------------

def _is_complete(
        pitches: Union[list, tuple],
        harmony: List[PitchClass]
    ) -> bool:
    
    """
    Check if the given pitches fully reifies the given harmony.
    """

    # get pitch classes
    pitch_classes = [pitch % 12 for pitch in pitches if pitch]

    # check completeness
    completeness = set(pitch_classes) >= set(harmony)

    return completeness


def is_complete(
        pitch_motif: PitchLine,
        harmony: List[PitchClass],
        exclude: List[Union[int, Tuple[int, int]]] = []
    ) -> bool:
    
    """
    Check if a pitch motif fully reifies the given harmony.
    """
    
    # not include the pitches at positions `exclude`
    if exclude:
        pitch_motif = deepcopy(pitch_motif)

        for position in exclude:
            _modify(pitch_motif, position, None, True)

    pitches = _extract(pitch_motif)
    completeness = _is_complete(pitches, harmony)
    return completeness


def _contour(
        pitch_motif: PitchLine,
        ordinal: List[Tuple[int, int]] = [],
    ) -> List[Optional[int]]:

    """
    Get the contour of a pitch motif.
    """

    pass
