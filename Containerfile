# Lucent OS — a calm, fast desktop for people leaving Windows.
# Base: Fedora Kinoite (KDE Plasma 6) bootable container, atomic updates with rollback.
#
# Tag checked against quay.io on 2026-11-08: 43, 44 and 45 are published and
# Fedora 45 is the current stable release.
ARG FEDORA_VERSION=45
ARG BASE_IMAGE=quay.io/fedora-ostree-desktops/kinoite

FROM ${BASE_IMAGE}:${FEDORA_VERSION}

LABEL org.opencontainers.image.title="Lucent OS" \
      org.opencontainers.image.description="Clean, fast KDE Plasma desktop for people leaving Windows (prototype)" \
      org.opencontainers.image.source="https://github.com/sidun-av/lucent-os" \
      org.opencontainers.image.licenses="Apache-2.0" \
      containers.bootc="1"

# Static configuration: Plasma defaults, look-and-feel, services, scripts.
COPY system_files/ /
# Migration wizard («Переезд с Windows»).
COPY migration-wizard/lucent_migrate/ /usr/lib/lucent/lucent_migrate/

# build.sh: declutter, fonts, Wine without wine-systemd (x86_64), ARM64EC Wine +
# FEX from COPR lacamar/wine-arm64ec (aarch64 only), LUCENT-BRIDGE HOOK, services.
RUN --mount=type=bind,source=.,target=/ctx,ro \
    /ctx/build_files/build.sh

RUN bootc container lint
