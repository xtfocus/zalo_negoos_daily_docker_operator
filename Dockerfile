FROM python:3.8.10

#RUN python -m venv /venv
#ENV PATH="/venv/bin:$PATH"

RUN curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
RUN apt-get update

RUN apt-get install -y nvidia-container-toolkit


RUN pip install --upgrade pip
RUN pip install torch==1.11.0+cu115 -f https://download.pytorch.org/whl/torch_stable.html

ENV VIRTUAL_ENV=/usr/local
WORKDIR /kedro_code

RUN apt-get update && apt-get -y install unixodbc curl debian-keyring

# installing ODBC 17 for mssql
RUN curl https://packages.microsoft.com/keys/microsoft.asc |  tee /etc/apt/trusted.gpg.d/microsoft.asc

RUN apt-get update

RUN curl https://packages.microsoft.com/config/debian/10/prod.list |  tee /etc/apt/sources.list.d/mssql-release.list

RUN  apt-get update
RUN  ACCEPT_EULA=Y apt-get install -y msodbcsql17

ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh


# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./zalo_chatlog_oos_negative_pipeline/requirements.txt /kedro_code/requirements.txt

RUN /root/.cargo/bin/uv pip install --system --no-cache -r /kedro_code/requirements.txt

COPY ./zalo_chatlog_oos_negative_pipeline /kedro_code

#ENTRYPOINT ["python", "app.py"]

