# Copyright (c) 2024 Katteli Inc. All rights reserved.
#
# All information contained herein is, and remains
# the property of Katteli Inc. All source code, intellectual and technical
# concepts contained herein are proprietary to Katteli Inc.
# and may be covered by domestic or foreign patents, and are protected
# by trade secret or copyright law.
#
# Any dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Katteli Inc.
import os
import ssl
import socket
import subprocess
import testflows.settings as settings
from testflows.exceptions import SSLConfigError
from testflows._core.cli.text import secondary


class Certificate:
    """SSL certificate and private key.
    Both are path to files on the file system.
    """

    def __init__(self, key, cert) -> None:
        self.key = key
        self.cert = cert


def default_ssl_dir():
    """Return default SSL directory."""
    return os.path.join(os.path.expanduser("~"), ".testflows", "ssl")


def get_ca_cert(dir=None):
    """Return CA certificate."""
    if dir is None:
        dir = default_ssl_dir()

    return Certificate(
        key=os.path.join(dir, "ca.key"), cert=os.path.join(dir, "ca.crt")
    )


def get_host_cert(dir=None):
    """Return host certificate."""
    if dir is None:
        dir = default_ssl_dir()

    return Certificate(
        key=os.path.join(dir, "host.key"), cert=os.path.join(dir, "host.crt")
    )


def new_context(purpose, dir=None):
    """Return SSL context with custom CA certificate and client certificate."""
    if dir is None:
        ssl_dir = default_ssl_dir()

    if not os.path.exists(ssl_dir):
        raise SSLConfigError(f"SSL directory '{ssl_dir}' not found")

    ca_cert = get_ca_cert()
    host_cert = get_host_cert()

    if not os.path.exists(ca_cert.cert):
        raise SSLConfigError(
            f"certificate authority SSL certificate '{ca_cert.cert}' not found"
        )
    if not os.path.exists(host_cert.cert):
        raise SSLConfigError(f"host SSL certificate '{host_cert.cert}' not found")
    if not os.path.exists(host_cert.key):
        raise SSLConfigError(f"host SSL private key '{host_cert.key}' not found")

    ssl_context = ssl.create_default_context(purpose=purpose, cafile=ca_cert.cert)

    ssl_context.load_cert_chain(
        certfile=host_cert.cert,
        keyfile=host_cert.key,
    )

    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    return ssl_context


def new_client_context(dir=None):
    """Return new client SSL context."""
    return new_context(purpose=ssl.Purpose.SERVER_AUTH, dir=dir)


def new_server_context(dir=None):
    """Return new server SSL context."""
    return new_context(purpose=ssl.Purpose.CLIENT_AUTH, dir=dir)


def new_ca_cert(dir, hostname=None, key_length=2048, days=3650, verbose=False):
    """Generate a CA's (certificate authority) private key
    and certificate in the given directory.
    """
    if hostname is None:
        hostname = socket.gethostname()

    ca_key = os.path.join(dir, "ca.key")
    ca_crt = os.path.join(dir, "ca.crt")

    command = f'openssl genrsa -out "{ca_key}" {key_length}'
    subprocess.check_call(command, stdout=subprocess.PIPE, shell=True)

    command = (
        "openssl req -new -x509"
        f" -days {days} -key '{ca_key}'"
        " -sha256 -extensions v3_ca"
        f" -out '{ca_crt}'"
        f" -subj '/O=testflows.com CA/CN={hostname}'"
    )
    if verbose:
        print(secondary(command, eol=""))
    subprocess.check_call(command, stdout=subprocess.PIPE, shell=True)

    return Certificate(key=ca_key, cert=ca_crt)


def new_host_cert(
    dir, ca_cert, hostname=None, ip=None, length=2048, days=3650, verbose=False
):
    """Generate host private key and host certificate in the given directory
    signed by the specified certificate authority."""

    if hostname is None:
        hostname = socket.gethostname()

    if ip is None:
        ip = socket.gethostbyname(hostname)

    host_key = os.path.join(dir, "host.key")
    host_crt = os.path.join(dir, "host.crt")
    host_csr = os.path.join(dir, "host.csr")

    if not os.path.exists(ca_cert.cert):
        raise SSLConfigError(
            f"certificate authority SSL certificate '{ca_cert.cert}' not found"
        )

    if not os.path.exists(ca_cert.key):
        raise SSLConfigError(
            f"certificate authority SSL private key '{ca_cert.key}' not found"
        )

    command = f"openssl genrsa -out '{host_key}' {length}"
    if verbose:
        print(secondary(command, eol=""))
    subprocess.check_call(command, stdout=subprocess.PIPE, shell=True)

    command = f"openssl req -sha256 -new -key '{host_key}' -out '{host_csr}' -subj '/O=testflows.com Hosts/CN={hostname}' -addext 'subjectAltName=IP:{ip}'"
    if verbose:
        print(secondary(command, eol=""))
    subprocess.check_call(command, stdout=subprocess.PIPE, shell=True)

    try:
        command = f"openssl x509 -sha256 -req -in '{host_csr}' -copy_extensions copy -CA '{ca_cert.cert}' -CAkey '{ca_cert.key}' -CAcreateserial -out '{host_crt}' -days {days}"
        if verbose:
            print(secondary(command, eol=""))
        subprocess.check_call(command, stdout=subprocess.PIPE, shell=True)
    finally:
        if os.path.exists(host_csr):
            os.remove(host_csr)

    return Certificate(key=host_key, cert=host_crt)


def show_cert(cert, dir=None):
    """Show certificate."""
    if dir is None:
        dir = default_ssl_dir()
    return subprocess.check_output(
        f"openssl x509 -noout -text -in '{os.path.join(dir, cert)}'",
        shell=True,
        text=True,
    )


def show_key(key, dir=None):
    """Show key."""
    if dir is None:
        dir = default_ssl_dir()
    return subprocess.check_output(
        f"openssl rsa -noout -text -in '{os.path.join(dir, key)}'",
        shell=True,
        text=True,
    )
