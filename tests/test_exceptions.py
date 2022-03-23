"""Contains tests for solrfixtures.exceptions"""

import pytest

from solrfixtures.exceptions import ChoicesWeightsLengthMismatch


@pytest.mark.parametrize('num_choices, num_weights, noun, exp_msg_pattern', [
    (10, 9, '', 'Mismatched number of choices (10) to choice weights (9).'),
    (10, 9, None, 'Mismatched number of choices (10) to choice weights (9).'),
    (5, 32, 'str_length',
     'Mismatched number of str_length choices (5) to choice weights (32).'),
])
def test_choicesweightslengthmismatch_error_string(num_choices, num_weights,
                                                   noun, exp_msg_pattern):
    with pytest.raises(ChoicesWeightsLengthMismatch) as excinfo:
        raise ChoicesWeightsLengthMismatch(num_choices, num_weights, noun)
    err_msg = str(excinfo.value)
    assert exp_msg_pattern in err_msg
