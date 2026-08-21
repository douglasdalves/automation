#!/usr/bin/env bash
set -euo pipefail

config_file="${1:?Usage: sync-configs.sh /path/to/sync.conf}"

while IFS='|' read -r app_name source_dir destination_dir files; do
    [[ -z "${app_name}" || "${app_name}" == \#* ]] && continue

    if [[ ! -d "${source_dir}" ]]; then
        printf 'Source directory does not exist for %s: %s\n' "${app_name}" "${source_dir}" >&2
        exit 1
    fi

    mkdir -p "${destination_dir}"

    IFS=',' read -ra file_patterns <<< "${files}"
    for file_pattern in "${file_patterns[@]}"; do
        if [[ "${file_pattern}" == *'*'* ]]; then
            source_files=("${source_dir}"/${file_pattern})
        else
            source_files=("${source_dir}/${file_pattern}")
        fi

        if [[ ! -e "${source_files[0]}" ]]; then
            printf 'File pattern does not match for %s: %s\n' "${app_name}" "${file_pattern}" >&2
            exit 1
        fi

        mode=755
        [[ "${file_pattern}" == *.conf ]] && mode=644
        install -m "${mode}" -- "${source_files[@]}" "${destination_dir}/"
    done

done < "${config_file}"
