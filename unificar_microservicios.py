import os
import json
import pandas as pd
from pathlib import Path

# Rutas de archivos
carpeta_json = Path("data")  # Carpeta donde están tus archivos *.json
archivo_tokens = carpeta_json / "token.json"

# Cargar tokens
with open(archivo_tokens, encoding="utf-8") as f:
    token_list = json.load(f)
token_map = {t["tokenname"].lower(): t for t in token_list}

# Función para mapear token según entorno
def get_token_info(token_base, env):
    env_map = {"dev": "dev", "qa": "uat", "master": "prd"}
    suffix = env_map.get(env, env)
    token_key = f"{token_base}{suffix}".lower()
    return token_map.get(token_key, {"tokens": "", "namespace": "", "status": ""})

# Recolectar datos
rows = []

for file in carpeta_json.glob("*-MICROSERVICES.json"):
    country = file.stem.split("-")[0]
    with open(file, encoding="utf-8") as f:
        content = json.load(f)

    for project in content.get("project", []):
        project_name = project.get("name")
        for ms in project.get("ms", []):
            repo_url = ms.get("repositoryUrl", "")
            build_mode = ms.get("buildConfigurationMode", "")
            token_base = ms.get("tokenOcp", "")
            config_str = ms.get("config", "{}")

            try:
                config = json.loads(config_str)
            except Exception:
                config = {}

            app_name = config.get("appName", "")
            ocp_label = config.get("ocpLabel", "")
            image_version = config.get("baseImageVersion", "")
            usage = config.get("usage", "")
            volumes = config.get("volumes", [])
            secrets = config.get("secrets", [])
            configmaps = config.get("configMaps", [])
            drs_enabled = config.get("drsDeployEnable", False)

            for env in ["dev", "qa", "master"]:
                quota = config.get(f"resQuotas{env}", [])
                if not quota:
                    continue
                quota = quota[0]

                token_info = get_token_info(token_base, env)

                row = {
                    "country": country,
                    "project_name": project_name,
                    "app_name": app_name,
                    "environment": env,
                    "repository_url": repo_url,
                    "build_mode": build_mode,
                    "usage": usage,
                    "ocp_label": ocp_label,
                    "image_version": image_version,
                    "token": token_info["tokens"],
                    "namespace": token_info["namespace"],
                    "token_status": token_info["status"],
                    "cpu_limits": quota.get("cpuLimits", ""),
                    "cpu_request": quota.get("cpuRequest", ""),
                    "memory_limits": quota.get("memoryLimits", ""),
                    "memory_request": quota.get("memoryRequest", ""),
                    "replicas": quota.get("replicas", ""),
                    "drs_enabled": drs_enabled,
                    "volume_paths": "|".join([v.get("mountPath", "") for v in volumes]),
                    "secret_names": "|".join([s.get("secretName", "") for s in secrets]),
                    "configmap_names": "|".join([c.get("configMapName", "") for c in configmaps]),
                }

                rows.append(row)

# Guardar CSV
df = pd.DataFrame(rows)
df.to_csv("microservicios_unificado.csv", index=False, encoding="utf-8")
print("✅ Archivo 'microservicios_unificado.csv' generado correctamente.")
