fauxdoc
=======

[![Build Status](https://github.com/unt-libraries/fauxdoc/actions/workflows/do-checks-and-tests.yml/badge.svg?branch=main)](https://github.com/unt-libraries/fauxdoc/actions)

* [About](#about)
* [Installation](#installation)
* [Basic Usage](#basic-usage)
* [Contributing](#contributing)
* [License](#license)

## About

*`fauxdoc`* is designed to help you efficiently generate fake (faux) record or document (doc) data conforming to bespoke requirements.

Fauxdoc is tested with Python versions 3.7 and above, including 3.11. It has almost no external requirements: if you are using Python 3.7, it requires typing_extensions and importlib_metadata to provide features that were added in 3.8. Otherwise, it requires nothing but the standard library.

### Why not Faker or Mimesis?

[Faker](https://faker.readthedocs.io) and [Mimesis](https://mimesis.name) are established tools for generating fake data, and they are way more "batteries included" than Fauxdoc. Why not just implement a set of custom data providers for one of these?

#### Dynamically Generating Bespoke Data

Whereas other libraries make it dead simple to produce values that recognizably correspond to real-world items or properties (colors, names, addresses, etc.), Fauxdoc helps you dial in on patterns or features that may only pertain to your use case. This is helpful if you're trying to test something specific, like forcing certain sets of edge cases.

Fauxdoc began as part of a utility for helping test and benchmark configurations for particular Solr collections. We wanted to test search performance by producing text that shared certain features of a live collection, such as using specific alphabets; having word, phrase, and/or sentence lengths (etc.) within certain limits; and having specific terms occur in certain specific distributions. And we wanted to be able to simulate facets by choosing data values from a finite list of random terms that would produce a term distribution similar to the real data. Even with Faker or Mimesis, we would have had to build most of this from scratch, anyway.

#### Field / Schema / Document-Set Control

Other libraries mostly focus on generating values in isolation, but Fauxdoc facilitates having more control at the `Field` and `Schema` levels. For example, when generating documents to use to benchmark Solr, we found that we wanted to be able to do things like control uniqueness on a per-field basis, control uniqueness across an entire document set, generate data based on values in other fields, and have better control over multi-valued fields.

#### Performant Extensibility

We wrote Fauxdoc knowing that we'd be using it to generate hundreds of thousands or millions of fake Solr documents at one time, so performance was a concern. However, Fauxdoc is also meant to be highly extensible, and it's easy for extensibility to come at the expense of performance. So, Fauxdoc classes are designed to allow performant extensibility. You generally have a choice: you can implement something as (e.g.) a wrapper that's conceptually simple but a bit slower, or you can implement the same feature using a custom class, with lower-level methods that are faster but a little less simple. It just depends on your use case and where you need the extra performance.

The built-in data providers (called `Emitters`) are designed to be as fast as we could make them. Their performance is roughly comparable to Mimesis', although this is an apples-to-oranges comparison. Like Mimesis, they are much faster than Faker.

[Top](#top)


## Installation

Install the latest published version of fauxdoc with:

```
python -m pip install fauxdoc
```

See [Contributing](#contributing) for the recommended installation process if you want to develop on fauxdoc. 

[Top](#top)


## Basic Usage

### Emitters

Conceptually, `Emitters` are like Faker or Mimesis `Providers`. They are the objects that output your data values: simply instantiate one and then call it. If you need multiple values at once, you can supply an integer when calling.

```python
from fauxdoc import emitters
myrandom = emitters.Choice(['a', 'b', 'c'], weights=[45, 45, 10])

myrandom()
# 'b'

myrandom(10)
# ['a', 'b', 'a', 'c', 'b', 'b', 'a', 'a', 'a', 'b'] 
```

Several emitter types are provided in `fauxdoc.emitters` that have general behavior and options. Above, the `Choice` emitter chooses randomly between multiple values, with optional weights and parameters to control uniqueness.

For more complex behavior, you can of course create your own Emitter classes using `fauxdoc.emitter.Emitter` as your base class. Mixins are provided in `fauxdoc.mixins` for standard ways of doing things (such as randomization).

### Fields

Each `Field` wraps an emitter instance and provides options to gate the output and/or generate multiple values. These options are themselves implemented as emitters. As with emitter instances, you also call a field instance to output values.

```python
from fauxdoc import emitters, profile

user_tags = ['adventure', 'yellow', 'awesome', 'food', 'action films']
user_tags_field = profile.Field(
  'user_tags',
  emitters.Choice(user_tags, replace_only_after_call=True),
  gate=emitters.chance(0.8),
  repeat=emitters.poisson_choice(range(1, 6), mu=3)
)

user_tags_field()
# ['action films', 'food', 'yellow']

user_tags_field()
# ['adventure', 'yellow', 'awesome', 'food']

user_tags_field()
# ['yellow', 'awesome', 'food']

user_tags_field()
# ['food', 'adventure', 'awesome', 'yellow']

user_tags_field()
# 
```

### Schema

Your `Schema` is a specific collection of field instances. Calling the schema instance generates data representing one full document (returned as a dictionary).

```python
import itertools
from fauxdoc import emitters, profile, dtrange

ENGLISH = emitters.make_alphabet([(ord('a'), ord('z'))])
GENRES = ['Science', 'Literature', 'Medicine', 'Fiction', 'Television']

myschema = profile.Schema(
  profile.Field('id', emitters.Iterative(lambda: itertools.count(1))),
  profile.Field(
    'title',
    emitters.WrapOne(
      emitters.Text(
        numwords_emitter=emitters.poisson_choice(range(1, 10), mu=2),
        word_emitter=emitters.Word(
          length_emitter=emitters.poisson_choice(range(1, 10), mu=5),
          alphabet_emitter=emitters.Choice(ENGLISH)
        )
      ),
      lambda title: title.capitalize()
    )
  ),
  profile.Field('doc_type', emitters.Choice(['report', 'article', 'book'])),
  profile.Field('date_created', emitters.Choice(dtrange.dtrange('1950-01-01', '2025-01-01'))),
  profile.Field(
    'genres',
    emitters.Choice(GENRES, replace_only_after_call=True),
    gate=emitters.chance(0.5),
    repeat=emitters.poisson_choice(range(1, 3), mu=1)
  )
)

myschema()
# {
#   'id': 1,
#   'title': 'Dvcoqh zbuaba',
#   'doc_type': 'book',
#   'date_created': datetime.date(1951, 8, 15),
#   'genres': ['Medicine', 'Fiction']
# }

myschema()
# {
#   'id': 2,
#   'title': 'Dird',
#   'doc_type': 'report',
#   'date_created': datetime.date(1998, 4, 6),
#   'genres': ['Fiction']
# }

myschema()
# {
#   'id': 3,
#   'title': 'Wvlptqk',
#   'doc_type': 'book',
#   'date_created': datetime.date(1977, 12, 10),
#   'genres': None
# }

myschema()
# {
#   'id': 4,
#   'title': 'Tnhkez',
#   'doc_type': 'article',
#   'date_created': datetime.date(1988, 1, 22),
#   'genres': None
# }

myschema()
# {
#   'id': 5,
#   'title': 'Ld gudv lnaxx',
#   'doc_type': 'article',
#   'date_created': datetime.date(1989, 9, 30),
#   'genres': ['Medicine']
# }
```

### Generating Data Based on Other Fields

For complex schemas, you may find generating values for each field in isolation to be too limiting. Fauxdoc allows you to create emitters that can access values generated in other fields. You can also create hidden fields, allowing you to generate a normalized or collective data value and then pull it into the appropriate de-normalized fields.

```python
import itertools
from fauxdoc import emitter, emitters, profile

def item_data_generator():
  for num in itertools.count(1):
    yield {
      'item_id': num,
      'barcode': 2000000000 + num
    }

myschema = profile.Schema(
  # This field is hidden. It generates data for 1 to 10 "items" that
  # the other fields then pull from.
  profile.Field(
    '__all_items',
    emitters.Iterative(item_data_generator),
    repeat=emitters.poisson_choice(range(1, 10), mu=3),
    hide=True,
  )
)

myschema.add_fields(
  profile.Field(
    'display_items',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: items[:3]
    )
  ),
  profile.Field(
    'more_items',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: items[3:] if len(items) > 3 else None
    )
  ),
  profile.Field(
    'has_more_items',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: bool(len(items) > 3)
    )
  ),
  profile.Field(
    'item_ids',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: [i['item_id'] for i in items]
    )
  ),
  profile.Field(
    'item_barcodes',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: [i['barcode'] for i in items]
    )
  )
)

myschema()
# {
#   'display_items': [
#     {'item_id': 1, 'barcode': 2000000001}
#   ],
#   'more_items': None,
#   'has_more_items': False,
#   'item_ids': [1],
#   'item_barcodes': [2000000001]
# }

myschema()
# {
#   'display_items': [
#     {'item_id': 2, 'barcode': 2000000002},
#     {'item_id': 3, 'barcode': 2000000003},
#     {'item_id': 4, 'barcode': 2000000004}
#   ],
#   'more_items': [
#     {'item_id': 5, 'barcode': 2000000005}
#   ],
#   'has_more_items': True,
#   'item_ids': [2, 3, 4, 5],
#   'item_barcodes': [2000000002, 2000000003, 2000000004, 2000000005]
# }
```

[Top](#top)


## Contributing

### Installing for Development and Testing

Fork the project on GitHub and then clone it locally:

```bash
git clone https://github.com/[your-github-account]/fauxdoc.git
```

All dependency and build information is defined in `pyproject.toml` and follows [PEP 621](https://peps.python.org/pep-0621/). From the fauxdoc root directory, you can install it as an editable project into your development environment with:

```bash
python -m pip install -e .[dev]
```

(The `[dev]` ensures it includes the optional development dependencies, namely pytest.)


### Running Tests

Run the full test suite in your active environment by invoking:

```bash
pytest
```

from the fauxdoc root directory.


#### Tox

Because this is a library, it needs to be tested against all supported environments for each update, not just one development environment. The tool we use for this is [tox](https://tox.wiki/en/latest/).

Rather than use a separate `tox.ini` file, I've opted to put the tox configuration directly in `pyproject.toml` (under the `[tool.tox]` table). There, I've defined several environments: flake8, pylint, and each of py37 through py311 using both the oldest possible dependencies and newest possible dependencies. When you run tox, you can target a specific environment, a specific list of environments, or all of them.

When tox runs, it automatically builds each virtual environment it needs, and then it runs whatever commands it needs within that environment (for linting, or testing, etc.). All you have to do is expose all the necessary Python binaries on the path, and tox will pick the correct one. My preferred way to manage this is with [pyenv](https://github.com/pyenv/pyenv) + [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv).

For example: Install these tools along with the Python versions you want to test against. Then:

1. Create an environment with tox installed. E.g.:
    ```
    pyenv virtualenv 3.10.8 tox-3.10.8
    pyenv activate
    python -m pip install tox
    ```
2. In the fauxdoc project repository root, create a file called `.python-version`. Add all of the Python versions you want to use, e.g., 3.7 to 3.11. For 3.10, use your `tox-3.10.8`. This should look something like this:
    ```
    3.7.15
    3.8.15
    3.9.15
    tox-3.10.8
    3.11.0
    ```
4. If `tox-3.10.8` is still activated, issue a `pyenv deactivate` command so that pyenv picks up what's in the file. (A manually-activated environment overrides anything set in a `.python-version` file.)
5. At this point you should have all five environments active at once in that directory. When you run `tox`, the tox in your `tox-3.10.8` environment will run, and it will pick up the appropriate binaries automatically (`python3.7` through `python3.11`) since they're all on the path.

Now you can just invoke tox to run linters and all the tests against all the environments:

```bash
tox
```

Or just run linters:

```bash
tox -e flake8,pylint_critical
```

Or run tests against a list of specific environments:

```bash
tox -e py39-oldest,py39-newest
```

[Top](#top)


## License

See the [LICENSE](LICENSE) file.

[Top](#top)
