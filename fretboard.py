# -*- coding: utf-8 -*-

import argparse
import random
from time import sleep
import sys
from enum import Enum
from functools import total_ordering
from typing import List


############
# Utils
############

def applyNTimes(f, x, n):
    state = x
    for i in range(n):
        state = f(state)
    return state

# from https://docs.python.org/3.10/library/enum.html#orderedenum
class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

# symbols: ♭ ♮ ♯

class Accidental(OrderedEnum):
    flat = 0
    natural = 1
    sharp = 2

    def __str__(self):
        match self:
            case Accidental.flat:
                return "♭"
            case Accidental.natural:
                return "♮"
            case Accidental.sharp:
                return "♯"

    def str_omit_natural(self):
        if self == Accidental.natural:
            return ""
        else:
            return str(self)

    @classmethod
    def from_string(cls, string):
        match string:
            case "♭":
                return Accidental.flat
            case "b":
                return Accidental.flat
            case "♮":
                return Accidental.natural
            case "♯":
                return Accidental.sharp
            case "#":
                return Accidental.sharp
            case other:
                raise ValueError("Invalid accidental symbol. String must be a single character, one of '♭', '♮', or '♯'")

''' handles G -> A.
    Assumes the argument is a single letter in uppercase, that is a valid note letter
'''
def next_letter(letter):
    if letter == "G":
        return "A"
    else:
        return chr(ord(letter) + 1)


''' A musical note.

    NOTE this will not behave correctly in the presence of B#, Cb, E#, or Fb. Also does not handle double sharps or double flats.
'''
@total_ordering
class Note:
    def __init__(self, letter, accidental=Accidental.natural):
        letter = letter.upper()
        if letter not in LETTER_NOTES:
            raise ValueError("Invalid note letter")
        self.letter = letter
        self.accidental = accidental

    def __eq__(self, other):
        return (self.letter, self.accidental) == (other.letter, other.accidental)

    def __lt__(self, other):
        return (self.letter, self.accidental) < (other.letter, other.accidental)

    def __key(self):
        return (self.letter, self.accidental)

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return self.letter + str(self.accidental)

    def str_omit_natural(self):
        return self.letter + self.accidental.str_omit_natural()

    # only returns sharps for now.
    def semitone_above(self):
        match self.accidental:
            case Accidental.natural:
                if self.letter not in CANT_BE_SHARP:
                    return Note(self.letter, Accidental.sharp)
                else:
                    # either B -> C or E -> F. Don't need to worry about 
                    # looping, that only happens at G -> A
                    return Note(next_letter(self.letter), Accidental.natural)
            case Accidental.sharp:
                # assumes we're not incrementing an invalid note eg B#.
                return Note(next_letter(self.letter), Accidental.natural)
            case Accidental.flat:
                return Note(self.letter, Accidental.natural)

    def semitones_above(self, n):
        return applyNTimes(lambda note: note.semitone_above(), self, n)

    def tone_above(self):
        return self.semitones_above(2)

    def tones_above(self, n):
        return self.semitones_above(2 * n)

    @classmethod
    def from_string(cls, string):
        match len(string):
            case 1: return Note(string, Accidental.natural)
            case 2:
                accidental = Accidental.from_string(string[1])
                return Note(string[0], accidental)
            case other:
                raise ValueError("Invalid note string.")

# for now these only work with sharps
def major_scale(tonic: Note) -> List[Note]:
    return [ tonic,
              tonic.semitones_above(2),
              tonic.semitones_above(4),
              tonic.semitones_above(5),
              tonic.semitones_above(7),
              tonic.semitones_above(9),
              tonic.semitones_above(11),
            ]

def natural_minor_scale(tonic: Note) -> List[Note]:
    return [ tonic,
              tonic.semitones_above(2),
              tonic.semitones_above(3),
              tonic.semitones_above(5),
              tonic.semitones_above(7),
              tonic.semitones_above(8),
              tonic.semitones_above(10),
            ]

############
# CONSTANTS
############

LETTER_NOTES = list("CDEFGAB")

# technically they can be, but it's less annoying to just use the enharmonic equivalent
CANT_BE_SHARP = set("BE")
CANT_BE_FLAT  = set("CF")

ALL_NOTES_SHARPS = sorted(
        [Note(letter, Accidental.natural) for letter in LETTER_NOTES] +
        [Note(letter, Accidental.sharp)
            for letter in LETTER_NOTES if letter not in CANT_BE_SHARP])

ALL_NOTES_FLATS = sorted(
        [Note(letter, Accidental.natural) for letter in LETTER_NOTES] +
        [Note(letter, Accidental.flat) 
            for letter in LETTER_NOTES if letter not in CANT_BE_FLAT])

# includes notes that are enharmonically equivalent, eg C♯ and D♭
ALL_NOTES = sorted(set(ALL_NOTES_SHARPS) | set(ALL_NOTES_FLATS))

# todo: support tonics on accidentals
MAJOR_SCALES = {tonic + " major": major_scale(Note(tonic)) for tonic in LETTER_NOTES}
NATURAL_MINOR_SCALES = {tonic + " minor": natural_minor_scale(Note(tonic)) for tonic in LETTER_NOTES}
SCALES = {"chromatic": ALL_NOTES} | MAJOR_SCALES | NATURAL_MINOR_SCALES

def quick_dirty_test_semitone_above():
    cases = [
            ("C", "C#"),
            ("E", "F"),
            ("F", "F#"),
            ("B", "C"),
            ("G#", "A"),
            ("G", "G#")
            ]

    for (note, expected) in cases:
        (note, expected) = Note.from_string(note), Note.from_string(expected)
        assert note.semitone_above() == expected

# TODO write a proper datatype and parser for scales
def normalize_scale_name(name: str) -> str:
    if name == "chromatic":
        return name
    else:
        if len(name) == 1:
            return name.upper() + " " + "major"
        elif len(name) == 2 and name[1] == "m":
            return name[0].upper() + " " + "minor"
        else:
            # eg "f major", "F major", "c minor"
            try:
                [letter, quality] = name.split()
            except ValueError as e:
                # the name is invalid - this will be handled in main
                return name
            return " ".join([letter.upper(), quality])


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--time', type=int, default=30)
    parser.add_argument('-s', '--scale', type=str, default="chromatic")

    args = parser.parse_args()
    args.scale = args.scale.lower()
    args.scale = normalize_scale_name(args.scale)

    # todo: scales starting on accidentals
    if args.scale in SCALES:
        scale = SCALES[args.scale]
    else:
        print("Sorry, I don't know about that scale yet. Here are the scales I know about:")
        for k in SCALES:
            print("- " + k)
        sys.exit()

    print(f"Choosing a random note from the {args.scale} scale every {args.time} seconds.")
    while True:
        print(random.choice(scale).str_omit_natural())
        print("")
        sleep(args.time)


if __name__ == '__main__':
    main()
