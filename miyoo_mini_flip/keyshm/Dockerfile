#docker build -t set_monitor_arm7 .
# mkdir -p output
#Linux : docker run --rm -v "$PWD/output":/output set_monitor_arm7 cp set_monitor /output/
#Windows : docker run --rm -v ${PWD}/output:/output set_monitor_arm7 cp set_monitor /output/

# Base image for ARMv7 Debian
FROM arm32v7/debian:buster

RUN sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    apt-get -o Acquire::Check-Valid-Until=false update

# Install build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        make \
        file \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /src

# Copy the source
COPY set_monitor.c .

# Build the binary
RUN gcc -Os -s -o set_monitor set_monitor.c -ldl -lpthread

# Default command (verify binary)
CMD ["file", "./set_monitor"]
