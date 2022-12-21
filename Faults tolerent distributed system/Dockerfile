#####################
# build docker:
# docker build -t hw4 .
#####################
#docker run -d -p 8080:8080 hw4
# docker run -d -p 8083:8080 --net=mynet --ip=10.0.0.3 -e VIEW="10.0.0.2:8080,10.0.0.3:8080" -e IP_PORT="10.0.0.3:8080" hw4
#
# docker run -d -p 8082:8080 --net=mynet --ip=10.0.0.2 -e VIEW="10.0.0.2:8080,10.0.0.3:8080" -e IP_PORT="10.0.0.2:8080" hw4
#
# docker run -d -p 8084:8080 -e VIEW="10.0.0.16:8082, 10.0.0.16:8083, 10.0.0.16:8084" -e IP_PORT=“10.0.0.16:8084” hw4
#####################
# STOP ALL
# docker stop $(docker ps -aq)
#####################
# to build mynet
# sudo docker network create --subnet=10.0.0.0/24 mynet
#####################
# to disconnect:
# docker container ls
# docker network disconnect mynet clever_mcclintock
# python3 hw4_test.py
#####################
# docker run -p 8082:8080 --net=mynet --ip=10.0.0.2 -e VIEW=10.0.0.2:8080,10.0.0.3:8080,10.0.0.4:8080,10.0.0.5:8080,10.0.0.6:8080 -e IP_PORT=10.0.0.2:8080 -e S=2 hw4
# docker run -p 8083:8080 --net=mynet --ip=10.0.0.3 -e VIEW=10.0.0.2:8080,10.0.0.3:8080,10.0.0.4:8080,10.0.0.5:8080,10.0.0.6:8080 -e IP_PORT=10.0.0.3:8080 -e S=2 hw4
# docker run -p 8084:8080 --net=mynet --ip=10.0.0.4 -e VIEW=10.0.0.2:8080,10.0.0.3:8080,10.0.0.4:8080,10.0.0.5:8080,10.0.0.6:8080 -e IP_PORT=10.0.0.4:8080 -e S=2 hw4
# docker run -p 8085:8080 --net=mynet --ip=10.0.0.5 -e VIEW=10.0.0.2:8080,10.0.0.3:8080,10.0.0.4:8080,10.0.0.5:8080,10.0.0.6:8080 -e IP_PORT=10.0.0.5:8080 -e S=2 hw4
# docker run -p 8086:8080 --net=mynet --ip=10.0.0.6 -e VIEW=10.0.0.2:8080,10.0.0.3:8080,10.0.0.4:8080,10.0.0.5:8080,10.0.0.6:8080 -e IP_PORT=10.0.0.6:8080 -e S=2 hw4
# docker run -p 8087:8080 --net=mynet --ip=10.0.0.7 -e VIEW=10.0.0.2:8080,10.0.0.3:8080,10.0.0.4:8080,10.0.0.5:8080,10.0.0.6:8080, 10.0.0.7:8080 -e IP_PORT=10.0.0.7:8080 -e S=2 hw4
# to PUT
# curl -X PUT -d 'val'="value" -d 'payload'='0,0,0,0,0' http://localhost:8086/keyValue-store/key1
# curl -X PUT -d 'ip_port'="10.0.0.4:8080" -d 'payload'='1,1' http://localhost:8082/view
# curl -X PUT -d 'val'="wt" -d 'payload'='1,1' -d 'timestamp'='0' http://localhost:8082/client_request add2
# to gET
# curl -i -H -d 'payload'='2.2' http://localhost:8083/keyValue-store/add
# to delete
# curl -X DELETE -d 'payload'='1,1' http://localhost:8082/keyValue-store/add
#####################
# to GET
# curl -i -H -d http://localhost:8083/shard/my_id 
# curl -i -H -d http://localhost:8083/shard/all_ids
# curl -i -H -d http://localhost:8086/shard/members/0
# curl -i -H -d http://localhost:8086/shard/count/0
#####################
# to PUT
# curl -X PUT -d 'num'="1" http://localhost:8083/shard/changeShardNumber
# curl -X PUT -d 'num'="2" http://localhost:8085/shard/changeShardNumber
# to DELETE clear
# curl -X DELETE -d 'ip_port'="10.0.0.5:8080" http://localhost:8082/clear
#####################
# to GET
# curl -i -H -d http://localhost:8085/view
# to PUT
# curl -X PUT -d 'ip_port'="10.0.0.7:8080" http://localhost:8082/view
# to DELETE
# curl -X DELETE -d 'ip_port'="10.0.0.5:8080" http://localhost:8082/view
#####################
#https://docs.docker.com/get-started/part2/#define-a-container-with-dockerfile

#Use an official Python runtime as a parent image
FROM python:2.7-slim

# Set the working directory to /hw1
WORKDIR /homework3

# Copy the current directory contents into the container at /hw1
ADD . /homework3

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install requests

RUN pip install -U 'gevent~=1.2.2'

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "app.py"]
