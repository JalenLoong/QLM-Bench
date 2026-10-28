# Sourced by job.sh. Defines legmanip_load_secrets FILE, which exports HF_TOKEN and
# WANDB_API_KEY from FILE without executing it and without printing any value.
#
# FILE holds KEY=VALUE lines (an optional "export " prefix and surrounding quotes are
# accepted; blank lines and # comments are skipped; other keys are ignored). It must
# be readable by its owner only (chmod 600), like the cluster's .secrets files.
# Sets LEGMANIP_SECRET_KEYS to the names that were loaded.

legmanip_load_secrets() {
  local file=$1 mode line key value loaded=()
  if [[ ! -f $file || ! -r $file ]]; then
    echo "[secrets] cannot read $file" >&2
    return 1
  fi
  mode=$(stat -c %a "$file")
  if ((8#$mode & 8#077)); then
    echo "[secrets] $file is mode $mode; run chmod 600 on it" >&2
    return 1
  fi
  while IFS= read -r line || [[ -n $line ]]; do
    line=${line#"${line%%[![:space:]]*}"}
    [[ -z $line || $line == \#* ]] && continue
    line=${line#export }
    key=${line%%=*}
    value=${line#*=}
    [[ $key == "$line" ]] && continue
    value=${value%$'\r'}
    if [[ $value == \"*\" || $value == \'*\' ]]; then
      value=${value:1:${#value}-2}
    fi
    case $key in
    HF_TOKEN | WANDB_API_KEY)
      if [[ -n $value ]]; then
        export "$key=$value"
        loaded+=("$key")
      fi
      ;;
    esac
  done <"$file"
  export LEGMANIP_SECRET_KEYS="${loaded[*]}"
  echo "[secrets] loaded from $file: ${LEGMANIP_SECRET_KEYS:-nothing}"
}
