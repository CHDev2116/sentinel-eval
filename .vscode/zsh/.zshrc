if [ -f "$HOME/.zshrc" ]; then
  source "$HOME/.zshrc"
fi

# Prefer explicit workspace venv from terminal env.
if [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/activate" ]; then
  source "$VIRTUAL_ENV/bin/activate"
else
  # Fallback: walk up from current directory to find nearest .venv.
  _cursor_dir="$PWD"
  while [ "$_cursor_dir" != "/" ]; do
    if [ -f "$_cursor_dir/.venv/bin/activate" ]; then
      source "$_cursor_dir/.venv/bin/activate"
      break
    fi
    _cursor_dir="$(dirname "$_cursor_dir")"
  done
  unset _cursor_dir
fi
