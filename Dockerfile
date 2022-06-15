FROM python:3.10

# the python image readme suggests this workdir:
WORKDIR /usr/src/app

COPY setup.py requirements*.txt README.md ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir -r requirements_dev.txt && \
    pip install --no-cache-dir -r requirements_testing.txt

COPY . .
