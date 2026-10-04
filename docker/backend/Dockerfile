ARG MAVEN_IMAGE=docker.m.daocloud.io/library/maven:3.9.12-eclipse-temurin-25
ARG JRE_IMAGE=docker.m.daocloud.io/library/eclipse-temurin:25-jre

FROM ${MAVEN_IMAGE} AS build

WORKDIR /workspace

COPY DurgInOutSystem/pom.xml ./
RUN mvn -B -DskipTests dependency:go-offline

COPY DurgInOutSystem/src ./src
RUN mvn -B -DskipTests package

FROM ${JRE_IMAGE}

ENV TZ=Asia/Shanghai
WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --uid 10001 app

COPY --from=build /workspace/target/DurgInOutSystem-0.0.1-SNAPSHOT.jar /app/app.jar

USER app
EXPOSE 9876

ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-jar", "/app/app.jar"]
