# Hugging Face Docker Space: serves the prebuilt app and fetches the lecture PDF at build time
# (the PDF is not stored in the Space repo).
FROM python:3.12-slim

RUN pip install --no-cache-dir pymupdf==1.26.*

WORKDIR /app
COPY site/ ./site/
COPY extract_pdf.py serve.py ./

ARG PDF_URL=https://antilogicalism.com/wp-content/uploads/2018/04/feynman-lectures.pdf
ADD ${PDF_URL} /tmp/full.pdf
RUN python extract_pdf.py /tmp/full.pdf site/vol1.pdf && rm /tmp/full.pdf

# Spaces run the container as uid 1000
RUN chown -R 1000:1000 /app
USER 1000

EXPOSE 7860
CMD ["python", "serve.py"]
