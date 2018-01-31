"""
Creator objects for creating data sets
"""

# Third Party
import unicodecsv as csv
import xlrd


class CsvCreator(object):
    """Create a dataset from a csv"""

    def __init__(self, name, file_):
        self.name = name
        self.csv_reader = csv.reader(file_)
        self.headers = next(self.csv_reader)

    def get_name(self):
        """Get the name of the dataset"""
        return self.name

    def get_headers(self):
        """Get the header values of the dataset"""
        return self.headers

    def get_rows(self):
        """Return an iterator of the datasets row values"""
        header_len = len(self.headers)
        for row in self.csv_reader:
            yield row[:header_len]


class XlsCreator(object):
    """Create a dataset from a csv"""

    def __init__(self, name, file_):
        self.name = name
        book = xlrd.open_workbook(file_contents=file_.read())
        self.sheet = book.sheet_by_index(0)
        self.headers = next(self.csv_reader)

    def get_name(self):
        """Get the name of the dataset"""
        return self.name

    def get_headers(self):
        """Get the header values of the dataset"""
        return self.sheet.row_values(0)

    def get_rows(self):
        """Return an iterator of the datasets row values"""
        for i in xrange(1, self.sheet.nrows):
            yield [unicode(v) for v in self.sheet.row_values(i)]


class CrowdsourceCreator(object):
    """Create a dataset from a crowdsource's responses"""

    def __init__(self, crowdsource):
        self.crowdsource = crowdsource
        self.metadata_keys = crowdsource.get_metadata_keys()

    def get_name(self):
        """Get the name of the dataset"""
        return self.crowdsource.title

    def get_headers(self):
        """Get the header values of the dataset"""
        return self.crowdsource.get_header_values(self.metadata_keys)

    def get_rows(self):
        """Return an iterator of the datasets row values"""
        for response in self.crowdsource.responses.all():
            yield response.get_values(self.metadata_keys)
