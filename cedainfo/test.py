import hashlib

user_str = 'kjdkfjdkfjdkf'

hash_string = hashlib.md5(user_str.encode("utf-8")).hexdigest()

print (hash_string)
