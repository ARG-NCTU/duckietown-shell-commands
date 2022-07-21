FROM argnctu/arg_tools:cpu

##################################### dts ######################################

RUN pip3 install duckietown-shell
RUN pip3 install -U arg-robotics-tools
RUN dts --set-version daffy
RUN export PATH=$PATH:/root/.local/bin
RUN which dts
#RUN dts
RUN apt-get update
RUN apt-get install ssh
