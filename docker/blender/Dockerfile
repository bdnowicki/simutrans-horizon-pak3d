# Headless Blender that builds the models of this pak 3D (scripts/build.sh).
# The official Linux archive from download.blender.org, pinned to one LTS release and checked against its published
# sha256 (the value below and the .sha256 file next to the archive must both match).
#   docker build -t blender-headless:5.2.4 docker/blender
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" blender-headless:5.2.4 \
#       blender -b --factory-startup -P /work/scripts/empire_state.py -- --out /work/models/empire_state.glb
FROM debian:13-slim

ARG BLENDER_VERSION=5.2.4
ARG BLENDER_SHA256=2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86

# runtime libraries of the official build (X11/GL are linked even in background mode); curl and xz only for the download
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
        libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 libgl1 libegl1 libglu1-mesa; \
    series="${BLENDER_VERSION%.*}"; \
    file="blender-${BLENDER_VERSION}-linux-x64.tar.xz"; \
    cd /tmp; \
    curl -fsSLO "https://download.blender.org/release/Blender${series}/${file}"; \
    curl -fsSL "https://download.blender.org/release/Blender${series}/blender-${BLENDER_VERSION}.sha256" -o published.sha256; \
    grep " ${file}\$" published.sha256 > archive.sha256; \
    echo "${BLENDER_SHA256}  ${file}" | sha256sum -c -; \
    sha256sum -c archive.sha256; \
    mkdir -p /opt/blender; \
    tar -xJf "${file}" -C /opt/blender --strip-components=1; \
    rm -f "${file}" published.sha256 archive.sha256; \
    apt-get purge -y curl xz-utils; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/*; \
    /opt/blender/blender --version

ENV PATH=/opt/blender:$PATH \
    HOME=/tmp
WORKDIR /work
CMD ["blender", "--version"]
