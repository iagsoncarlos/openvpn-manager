#!/bin/bash
set -e

# Self-contained .deb builder para OpenVPN Manager
# 1. Baixa wheels das dependências
# 2. Copia para a pasta do pacote
# 3. Gera o .deb com tudo incluso

VERSION=$(cat VERSION)
BUILD_DIR="dist"
WHEELS_DIR="$BUILD_DIR/wheels"

# Limpa e prepara
rm -rf "$BUILD_DIR/wheels"
mkdir -p "$WHEELS_DIR"

# Baixa as dependências como wheels
pip3 download --dest "$WHEELS_DIR" --prefer-binary PyQt6>=6.4.0

# Copia os wheels para o local do pacote
mkdir -p debian/openvpn-manager/usr/share/openvpn-manager/wheels
cp $WHEELS_DIR/*.whl debian/openvpn-manager/usr/share/openvpn-manager/wheels/

# Gera o .deb normalmente
# (usa o debian/rules padrão, que já instala os wheels e scripts)
dpkg-buildpackage -b -uc -us

# Limpa wheels temporários do diretório do pacote (opcional)
rm -rf debian/openvpn-manager/usr/share/openvpn-manager/wheels/*

echo "\n✅ Self-contained .deb gerado! Veja ../openvpn-manager_${VERSION}-1_all.deb"
