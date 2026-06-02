# Streamlit dashboard image (GeoPandas + Folium). Deploys to Hugging Face Spaces
# (Docker SDK, port 7860). pyogrio wheels bundle GDAL — no system geo libs needed.
FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY --chown=user . .

EXPOSE 7860
CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=7860", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
