import sys

from keycloakutils.password import generate_hash_data


if __name__ == "__main__":

    print(generate_hash_data(sys.argv[0]))
