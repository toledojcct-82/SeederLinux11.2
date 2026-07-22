#!/usr/bin/env python3
"""
SeederLinux Agent - Check-in periodico
======================================
Agente Python que faz check-in com o servidor SeederLinux, enviando
informacoes da estacao e baixando bundles de configuracao quando disponivel.

Suporta certificados autoassinados via --no-check-certificate ou
no_check_certificate = true no arquivo agent.conf.
"""

import argparse
import json
import os
import platform
import socket
import ssl
import subprocess
import sys
import urllib.request
import urllib.error
from configparser import ConfigParser

CONFIG_FILE = "/etc/seeder/agent.conf"
TIMEOUT = 30


def load_config(config_path=CONFIG_FILE):
    """Carrega configuracao do arquivo agent.conf."""
    config = {
        "url": None,
        "no_check_certificate": False,
    }

    if not os.path.exists(config_path):
        return config

    parser = ConfigParser()
    parser.read(config_path)

    if parser.has_section("server"):
        if parser.has_option("server", "url"):
            config["url"] = parser.get("server", "url").strip()
        if parser.has_option("server", "no_check_certificate"):
            raw = parser.get("server", "no_check_certificate").strip().lower()
            config["no_check_certificate"] = raw in ("true", "1", "yes", "on")

    return config


def create_ssl_context(no_check=False):
    """Cria contexto SSL. Se no_check=True, desativa verificacao de certificado."""
    if no_check:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None


def get_system_info():
    """Coleta informacoes basicas da estacao."""
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }

    try:
        info["ip_address"] = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        info["ip_address"] = "unknown"

    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    info["os"] = line.split("=", 1)[1].strip().strip('"')
                    break
    except (IOError, OSError):
        info["os"] = "unknown"

    try:
        result = subprocess.run(
            ["dmidecode", "-s", "system-serial-number"],
            capture_output=True, text=True, timeout=5
        )
        info["serial"] = result.stdout.strip() or "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        info["serial"] = "unknown"

    return info


def checkin(server_url, org, no_check_cert=False):
    """Envia check-in ao servidor e retorna a resposta JSON."""
    info = get_system_info()
    info["org"] = org

    payload = json.dumps(info).encode("utf-8")
    endpoint = server_url.rstrip("/") + "/api/agent/checkin"

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "SeederLinux-Agent/1.0",
        },
        method="POST",
    )

    ssl_context = create_ssl_context(no_check_cert)

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_context) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code}: {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"ERRO de conexao: {e.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print("ERRO: Resposta invalida do servidor (JSON invalido)", file=sys.stderr)
        return None


def download_bundle(server_url, bundle_url, no_check_cert=False):
    """Baixa um bundle de configuracao do servidor."""
    if bundle_url.startswith("/"):
        url = server_url.rstrip("/") + bundle_url
    elif bundle_url.startswith("http"):
        url = bundle_url
    else:
        url = server_url.rstrip("/") + "/" + bundle_url.lstrip("/")

    req = urllib.request.Request(url, headers={"User-Agent": "SeederLinux-Agent/1.0"})
    ssl_context = create_ssl_context(no_check_cert)

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_context) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code} ao baixar bundle: {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"ERRO de conexao ao baixar bundle: {e.reason}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="SeederLinux Agent - Check-in periodico"
    )
    parser.add_argument(
        "--org", "-o",
        help="Acronimo da organizacao (OM)"
    )
    parser.add_argument(
        "--server", "-s",
        help="URL do servidor SeederLinux (sobrescreve agent.conf)"
    )
    parser.add_argument(
        "--no-check-certificate", "-k",
        action="store_true",
        help="Disable SSL certificate verification"
    )
    parser.add_argument(
        "--config", "-c",
        default=CONFIG_FILE,
        help=f"Caminho do arquivo de configuracao (padrao: {CONFIG_FILE})"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Saida detalhada"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    server_url = args.server or config.get("url")
    if not server_url:
        print("ERRO: URL do servidor nao definida. Use --server ou configure agent.conf.",
              file=sys.stderr)
        sys.exit(1)

    org = args.org or config.get("org", "")
    if not org:
        print("ERRO: Organizacao nao definida. Use --org ou configure agent.conf.",
              file=sys.stderr)
        sys.exit(1)

    no_check_cert = args.no_check_certificate or config.get("no_check_certificate", False)

    if args.verbose:
        print(f">>> Servidor: {server_url}")
        print(f">>> Organizacao: {org}")
        print(f">>> Verificar certificado: {not no_check_cert}")
        print(f">>> Enviando check-in...")

    result = checkin(server_url, org, no_check_cert)
    if result is None:
        print(">>> Check-in falhou.", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f">>> Resposta: {json.dumps(result, indent=2)}")

    if result.get("bundle_url"):
        if args.verbose:
            print(f">>> Baixando bundle: {result['bundle_url']}")
        bundle_data = download_bundle(server_url, result["bundle_url"], no_check_cert)
        if bundle_data is None:
            print(">>> Falha ao baixar bundle.", file=sys.stderr)
            sys.exit(1)

        bundle_path = "/tmp/seeder-bundle.sh"
        with open(bundle_path, "wb") as f:
            f.write(bundle_data)
        os.chmod(bundle_path, 0o755)

        if args.verbose:
            print(f">>> Bundle salvo em {bundle_path}")

        try:
            subprocess.run([bundle_path], timeout=300, check=False)
            if args.verbose:
                print(">>> Bundle executado.")
        except subprocess.TimeoutExpired:
            print(">>> AVISO: Execucao do bundle expirou.", file=sys.stderr)
        except OSError as e:
            print(f">>> ERRO ao executar bundle: {e}", file=sys.stderr)

    print(">>> Check-in concluido.")


if __name__ == "__main__":
    main()
