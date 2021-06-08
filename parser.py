import xmltodict
import argparse
import requests
import pprint
import json
import re


class FeedParser:

    id = 0
    __counter = 0
    __url_pattern = r"(?:(?:http[s]?):\/\/)?[\w\/\-?=%.]+\.[\w\/\-&?=%.]+"
    __feed_loaded = False

    def __init__(self, url):
        self._url = self.__validate_url(url)

    def __validate_url(self, url):
        found = tuple(re.finditer(self.__url_pattern, url, re.MULTILINE))
        if len(found) != 1:
            raise ValueError("Provided URL is not valid")
        return url

    def __load_feed(self):
        req = requests.get(self._url)
        print(f"{self._url}\n\tSTATUS CODE: {req.status_code}\n")
        if req.status_code != 200:
            raise ResourceWarning(f"The {self._url} is unreachable")
        FeedParser.__counter += 1
        self.id = FeedParser.__counter
        with open(f'f{self.id}.xml', 'w', encoding="utf-8") as file:
            file.write(req.text)
        self.__feed_loaded = True
        return f'f{self.id}.xml'

    @property
    def __feed(self):
        if self.__feed_loaded:
            return f'f{self.id}.xml'
        return self.__load_feed()

    @property
    def xml_as_dict(self):
        with open(self.__feed) as xml:
            as_dict = json.loads(json.dumps(xmltodict.parse(xml.read(), process_namespaces=True)))
        unpacked = tuple(FeedParser.extract_nested_values("ROOT", as_dict))
        unique = set(unpacked)
        print(f"{self.__feed} contains {len(unpacked)} values which {len(unique)} are unique")
        return unique

    @staticmethod
    def extract_nested_values(key, value):
        if isinstance(value, list):
            for it in value:
                yield from FeedParser.extract_nested_values(key, it)
        elif isinstance(value, dict):
            for k, v in value.items():
                yield from FeedParser.extract_nested_values(f"{key} --> {k}", v)
        else:
            yield key, value

    def compare(self, other):
        print("\n----------------------------------------\n")
        unpacked_first_feed = self.xml_as_dict
        print("\n----------------------------------------\n")
        unpacked_second_feed = other.xml_as_dict
        print("\n----------------------------------------\n")
        with open(f'f{self.id}_unique.txt', 'w') as file:
            file.writelines(pprint.pformat(unpacked_first_feed - unpacked_second_feed))
        with open(f'f{other.id}_unique.txt', 'w') as file:
            file.writelines(pprint.pformat(unpacked_second_feed - unpacked_first_feed))
        print(f"Diffs successfully logged into f{self.id}_unique.txt and f{other.id}_unique.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f1', '--feed1', help='Specify url for first feed file')
    parser.add_argument('-f2', '--feed2', help='Specify url for second feed file')

    feed1 = FeedParser(parser.parse_args().feed1)
    feed2 = FeedParser(parser.parse_args().feed2)
    feed1.compare(feed2)
