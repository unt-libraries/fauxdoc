"""
Generate document set fixtures for Solr testing.
"""
class SolrFixtureFactory(object):
    """
    Class that creates documents to be used in Solr-related test
    fixtures. Data created conforms to a particular
    `profile.SolrProfile` object, passed in on initialization.
    """
    def __init__(self, profile):
        """
        Initialize a `SolrFixtureFactory` object. `profile` is the
        `profile.SolrProfile` object to use for generating data.
        """
        self.profile = profile
        self.conn = self.profile.conn

    def _make_doc(self, documents, field_gen_overrides):
        doc = {}
        for fname, default_gen in self.profile.field_gens.items():
            gen = field_gen_overrides.get(fname, default_gen)
            if gen is not None:
                field = self.profile.fields[fname]
                value = field.gen_value(gen, doc, documents)
                if value is not None:
                    doc[fname] = value
        return doc

    def make_more(self, docset, number, report_every=0, **field_gen_overrides):
        """
        Make a new set (list) of documents that are a subset of some
        existing set.

        `docset`: The list of existing docs. These are used when
        determining uniqueness for the new docset but is NOT modified.

        `number`: How many new documents you want to create.

        `field_gen_overrides`: Set of kwargs for the gens you want to
        use to generate this batch of documents. E.g., fieldname=gen.
        These override whatever defaults you set on the profile.

        `report_every`: If set, prints a one-line status report to
        stdout after finishing every N docs. (E.g., report_every=1000
        prints an update every 1000 documents.) Passing a falsey value
        (0, None) silences this.

        Returns a list containing only the newly-created documents.
        """
        full_docset = list(docset)
        for i in range(0, number):
            if report_every and i and i % report_every == 0:
                print('  Finished {} of {}.'.format(i, number))
            try:
                doc = self._make_doc(full_docset, field_gen_overrides)
            except self.profile.Field.ViolatesUniqueness:
                break
            else:
                full_docset.append(doc)
        return full_docset[len(docset):]

    def make(self, number, **field_gen_overrides):
        """
        Make a new set (list) of documents. Calls the `make_more` method
        using an empty initial list. (See `make_more` for more info.)
        """
        self.profile.reset_fields()
        return self.make_more([], number, **field_gen_overrides)

