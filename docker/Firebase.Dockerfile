FROM eclipse-temurin:21-jre@sha256:0b99b3376fbb50dbf9c0af8535fdd5b8eb0d3fdfc8b1e4967f383b6919f6901a AS java
FROM node:22.23.4-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da
COPY --from=java /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk PATH=/opt/java/openjdk/bin:$PATH
RUN --mount=type=cache,id=fullstyle-portfolio-npm-firebase,target=/root/.npm npm install --global firebase-tools@14.2.1 && firebase setup:emulators:firestore
WORKDIR /emulators
COPY docker/firebase.json docker/firestore.rules ./
CMD ["firebase", "emulators:start", "--only", "auth,firestore", "--project", "demo-fullstyle"]
