FROM rust:bullseye AS builder

WORKDIR /app

COPY . .

RUN cargo build --release --bin discord-bot


FROM debian:bullseye-slim

RUN apt-get update \
    && apt-get install -y openssl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN update-ca-certificates

WORKDIR /app

COPY --from=builder /app/target/release/discord-bot /usr/local/bin
ENTRYPOINT ["/usr/local/bin/discord-bot"]
