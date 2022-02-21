"""Contains custom Exception classes for solrfixtures."""


class ChoicesWeightsLengthMismatch(Exception):
    """Exception class for mismatched # of weights to # of choices.

    Subclasses of BaseRandomEmitter make heavy use of random.choices
    with optional weights arguments to provide for weighted random
    selection. If the number of weights provided and number of choices
    in the population do not match, random.choices will raise an error.
    Sometimes we want to validate this before making that
    random.choices call, such as during emitter __init__. If there is a
    mismatch, then we raise this exception.

    Attributes:
        num_choices: The total length of the population sequence.
        num_weights: The total (incorrect) length of the weights seq.
        noun: (Optional.) A singular noun or noun phrase describing
            what the choices population represents. It should make
            sense to say "[noun] choices". If not provided, we just say
            "choices".
    """

    def __init__(self,
                 num_choices: int,
                 num_weights: int,
                 noun: str = '') -> None:
        """Inits ChoiceWeightsLengthError with needed nums and noun."""
        self.num_choices = num_choices
        self.num_weights = num_weights
        self.noun = noun

    def __str__(self) -> str:
        """Generates an appropriate error message from attributes."""
        choices_phrase = f'{self.noun} choices' if self.noun else 'choices'
        return (
            f'Mismatched number of {choices_phrase} ({self.num_choices}) to '
            f'choice weights ({self.num_weights}). These amounts must match.'
        )
