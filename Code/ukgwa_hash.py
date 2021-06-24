import hashlib

class Hasher:

    def __init__(self, hash_function='md5', partitions=5):

        self._available_functions = {'md5' : hashlib.md5, 'sha1' : hashlib.sha1 , 'sha512' : hashlib.sha512,
                'blake2b' : hashlib.blake2b, 'blake2s' : hashlib.blake2s}
        if hash_function in self._available_functions:
            self.hash_function = self._available_functions[hash_function]
        else:
            print("Available functions are:", self.get_available_functions())
        self.partitions = partitions

    def get_available_functions(self):
        return self._available_functions

    def get_hash(self, *args):
        H = None
        for value in args:
            if value is None:
                value = ""
            value = repr(value).encode('utf-8')
            if H is None:
                H = self.hash_function(value)
            else:
                H.update(value)
        return H.hexdigest()

    def get_hash_partition(self, hash_value):
        return int(hash_value, 16) % self.partitions


