#!/usr/bin/env bash
set -euo pipefail

config_file="${1:?Usage: sync-configs.sh /path/to/sync.conf}"

while IFS='|' read -r app_name source_dir destination_dir; do
    [[ -z "${app_name}" || "${app_name}" == \#* ]] && continue

    if [[ ! -d "${source_dir}" ]]; then
        printf 'Source directory does not exist for %s: %s\n' "${app_name}" "${source_dir}" >&2
        exit 1
    fi

    mkdir -p "${destination_dir}"
    find "${destination_dir}" -maxdepth 1 -type f -name '*.yaml' -delete

    yaml_files=("${source_dir}"/*.yaml)
    if [[ -e "${yaml_files[0]}" ]]; then
        cp -- "${yaml_files[@]}" "${destination_dir}/"
    fi

done < "${config_file}"
