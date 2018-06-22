FROM tomcat:7.0-jre8

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y \
  git \
  maven \
  openjdk-8-jdk

WORKDIR /root

# TEAMENGINE
RUN git clone https://github.com/opengeospatial/teamengine

WORKDIR /root/teamengine
RUN git checkout 4.10
RUN mvn install

RUN cd teamengine-web/target/ && unzip -q teamengine.war -d /usr/local/tomcat/webapps/teamengine
RUN cd teamengine-web/target/ && unzip -q teamengine-common-libs.zip -d /usr/local/tomcat/lib
RUN cd teamengine-console/target/ && unzip -q teamengine-console-*-base.zip -d /root/te_base

# WMS 1.3.0
WORKDIR /root/
RUN git clone https://github.com/opengeospatial/ets-wms13
WORKDIR /root/ets-wms13
RUN git checkout 1.22
RUN mvn install

RUN cd target && unzip -q ets-wms13-*-ctl.zip -d /root/te_base/scripts
RUN mkdir -p /root/te_base/resources/lib
RUN cp target/ets-wms13-1.22-site.jar /root/te_base/resources/lib
RUN cp target/ets-wms13-1.22.jar /root/te_base/resources/lib

# START
ENV JAVA_OPTS="-Xms1024m -Xmx2048m -DTE_BASE=/root/te_base/"
CMD ["catalina.sh", "run"]
