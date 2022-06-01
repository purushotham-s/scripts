#!/usr/bin/python3
import os, sys, optparse, subprocess, shutil, yaml, base64, logging
from OpenSSL import crypto, SSL
import warnings

# To supress OpenSSL warning about using text passphrase
warnings.filterwarnings("ignore", category=DeprecationWarning)

def generate_key(type, bits):
        try:
                key = crypto.PKey()
                key.generate_key(type, bits)
        except Exception as error:
                print(f"Unable to generate key, Error: {error}")
        return key

def generate_files(filename, request):
        try:
                with open(filename, "wb") as f:
                        if ".csr" in filename:
                                f.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, request))
                        elif ".key" in filename:
                                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, request))
        except Exception as error:
                print(f"Failed to create CSR/Key files, Error: {error}")

def generate_csr(hostname):
        try:
            csrfile = f'{hostname}.csr'
            keyfile = f'{hostname}.key'
            TYPE_RSA = crypto.TYPE_RSA
            req = crypto.X509Req()
            req.get_subject().countryName = 'REPLACE_ME'
            req.get_subject().stateOrProvinceName = 'REPLACE_ME'
            req.get_subject().localityName = 'REPLACE_ME'
            req.get_subject().organizationName = 'REPLACE_ME'
            req.get_subject().CN = hostname
            key = generate_key(TYPE_RSA, 2048)
            req.set_pubkey(key)
            req.sign(key, "sha1")
            generate_files(csrfile, req)
            generate_files(keyfile, key)
        except Exception as error:
                print(f'Error generating CSR: {error}')

def request_cert(hostname):
    try:
        pass  # TODO - Add options to generate OpenSSL cert
    except Exception as error:
        print(f'Error requesting certs: {error}')

def create_pkcs12(hostname, keystore_pass):
        try:
                with open(f"{hostname}.pem", 'r') as file:
                        cert = file.read()
                with open(f"{hostname}.key", 'r') as file:
                        key = file.read()
                pkcs12 = crypto.PKCS12()
                pkcs12.set_certificate(crypto.load_certificate(crypto.FILETYPE_PEM, cert))
                pkcs12.set_privatekey(crypto.load_privatekey(crypto.FILETYPE_PEM, key))
                pkcs12_bin = pkcs12.export(passphrase=keystore_pass)
                with open(f"{hostname}.p12", 'wb') as file:
                        file.write(pkcs12_bin)
        except Exception as error:
                print(f'Error creating pkcs12: {error}')

def create_keystore(hostname, keystore_pass):
        try:
                subprocess.run(['keytool', '-importkeystore', '-srckeystore', f'{hostname}.p12', '-srcstoretype',\
                                                 'jks', '-destkeystore', f'{hostname}.jks', '-deststorepass', f'{keystore_pass}', \
                                                 '-srcstorepass', f'{keystore_pass}', '-noprompt'])
        except Exception as error:
                print(f'Error creating keystore: {error}')

def generate_secrets_file(hostname, keystore_pass):
        try:
                with open(f'{hostname}.jks', 'rb+') as file:
                        keystore = base64.b64encode(bytes(file.read()))
                service_name = hostname.split('.')[0]
                keystore = str(keystore, 'utf-8').replace('\n','')
                data = {service_name: {'keystore': keystore}}
        except Exception as error:
                print(f'Error generating secret: {error}')
        return data

def encrypt_secrets_file():
        try:
                subprocess.call(['helm', 'secrets', 'enc', 'secrets.yaml'])
        except Exception as error:
                print(f"Error encrypting secrets file with helm: {error}")

def check_prerequisites(no_cert_gen=False):
        try:
                if not os.path.exists('/usr/local/bin/helm'):
                        raise Exception("Helm not found, please install it.")
                if not os.path.exists('/usr/bin/keytool'):
                        raise Exception("Keytool not found, please install it.")
        except Exception as error:
                print(f"Error while checking for prerequisites: {error}")
                sys.exit(1)

def create_argument_parser():
        parser = optparse.OptionParser(usage='usage: %prog [options] arguments',
                                                                        description=("Script to generate Certs and Helm secrets file"))

        parser.add_option('--host', '-s',
                                                action='store',
                                                dest='hostname',
                                                help=("Hostname to create certs and secret for "\
                                                        "Ex: --host service.example.com"))

        parser.add_option('--file', '-f',
                                                action='store',
                        dest='hosts_file',
                        help=('Get hostnames from a file, where hostnames are '\
                                        'listed on individual lines'))

        parser.add_option('--encrypt',
                                                action='store_true',
                                                dest='encrypt',
                                                help='Encrypt secrets file')

        parser.add_option('--keystore-pass', '-p',
                                                action='store',
                                                dest='keystore_pass',
                                                help='Passphrase for Keystore')

        parser.add_option('--no-cert-gen', '-q',
                                                action='store_true',
                                                dest='no_cert_gen',
                                                help=('Skips certificate generation and creates secrets file with '\
                                                                'certs present in current directory'))
        return parser

def main():
        try:
                data = {}
                option_parser = create_argument_parser()
                options = option_parser.parse_args()[0]
                logging.basicConfig(filename=f'{sys.argv[0]}.log', level=logging.INFO, \
                                                        format='%(asctime)s - %(levelname)s - %(message)s')
                logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

                if len(sys.argv) < 3 and not options.keystore_pass:
                        option_parser.print_help()
                        sys.exit(1)
                else:
                        hostname = options.hostname
                        keystore_pass = options.keystore_pass
                        no_cert_gen = options.no_cert_gen

                if options.no_cert_gen:
                        check_prerequisites(no_cert_gen=True)
                else:
                        check_prerequisites()

                if options.hostname:
                        if not no_cert_gen:
                                generate_csr(hostname)
                                request_cert(hostname)
                        create_pkcs12(hostname, keystore_pass)
                        create_keystore(hostname, keystore_pass)
                        data.update(generate_secrets_file(hostname, keystore_pass))
                        with open('secrets.yaml', 'w') as file:
                                yaml.dump(data, file)

                if options.hosts_file:
                        hosts_file = options.hosts_file
                        if not os.path.exists(hosts_file):
                                raise Exception(f"File not found: {hosts_file}")
                        for hostname in open(hosts_file, 'r'):
                                hostname = hostname.replace("\n", "")
                                if not no_cert_gen:
                                        generate_csr(hostname)
                                        request_cert(hostname)
                                create_pkcs12(hostname, keystore_pass)
                                create_keystore(hostname, keystore_pass)
                                data.update(generate_secrets_file(hostname, keystore_pass))
                        with open('secrets.yaml', 'w') as file:
                                yaml.dump(data, file)

                if options.encrypt:
                        encrypt_secrets_file()

        except Exception as error:
                print(f"Error: {error}")

if __name__ == '__main__':
        main()
